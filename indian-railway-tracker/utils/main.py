import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from kafka import KafkaConsumer, KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import KafkaError, TopicAlreadyExistsError
from concurrent.futures import ThreadPoolExecutor
import threading

# ============================================================
# Logging Configuration
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("TrainStatusService")

# ============================================================
# Constants
# ============================================================

BASE_URL: str = "https://easy-rail.onrender.com/"
KAFKA_BOOTSTRAP_SERVERS = ["localhost:9092"]
LIVE_STATUS_TOPIC = "live-train-status"
CONSUME_TOPIC = "train-numbers"


# ============================================================
# API Response Normalizer
# ============================================================

def normalize_api_response(resp: Any) -> Any:
    """
    Normalize API response into a consistent structure.
    - If dict with {"success": true}, return `data` if present.
    - If dict without success flag, return dict as-is.
    - If list/tuple, return as-is.
    - Else, return as string.
    """
    if isinstance(resp, dict):
        if resp.get("success") is True:
            logger.info("Got Success")
            return resp.get("data", resp)
        logger.info("Didn't get Success")
        return resp

    elif isinstance(resp, (list, tuple)):
        resp_list = list(resp)  # convert once
        logger.info("It is a List: %s elements", len(resp_list))

        if len(resp_list) >= 2:
            logger.info("First 2 elements: %s", resp_list[:2])
        elif len(resp_list) == 1:
            logger.info("Single element: %s", resp_list[0])
        else:
            logger.info("Empty list/tuple")

        return resp

    else:
        return str(resp)




# ============================================================
# Kafka Topic Creation
# ============================================================

def create_topic_if_not_exists(topic_name: str, num_partitions: int = 1, replication_factor: int = 1):
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        topic_list = [NewTopic(name=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)]
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        logger.info("Topic created: %s", topic_name)
    except TopicAlreadyExistsError:
        logger.info("Topic already exists: %s", topic_name)
    except KafkaError as ke:
        logger.error("Kafka error while creating topic: %s | Error: %s", topic_name, ke)
    finally:
        if 'admin_client' in locals():
            admin_client.close()


# ============================================================
# API Utilities
# ============================================================

def call_api(
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = 10,
) -> Optional[Dict[str, Any]]:
    """
    Calls the given API endpoint and returns the JSON response.

    Args:
        endpoint (str): API endpoint path after BASE_URL (e.g., "trainInfo").
        method (str, optional): HTTP method ("GET" or "POST"). Defaults to "GET".
        params (dict, optional): Query parameters for GET requests. Defaults to None.
        payload (dict, optional): JSON body for POST requests. Defaults to None.
        timeout (int, optional): Timeout in seconds. Defaults to 10.

    Returns:
        dict | None: Parsed JSON response if successful, otherwise None.
    """
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        else:
            logger.error("Unsupported HTTP method: %s", method)
            return None

        response.raise_for_status()
        data = response.json()

        logger.info(
            "API Call Success | Endpoint: %s | Method: %s | Params: %s | Payload: %s",
            endpoint, method, params, payload
        )

        return data

    except requests.exceptions.Timeout:
        logger.error("API Timeout | Endpoint: %s | Params: %s", endpoint, params)
    except requests.exceptions.ConnectionError as ce:
        logger.error("API Connection Error | Endpoint: %s | Error: %s", endpoint, ce)
    except requests.exceptions.HTTPError as he:
        logger.error("API HTTP Error | Endpoint: %s | Status: %s", endpoint, he.response.status_code)
    except requests.exceptions.RequestException as re:
        logger.error("API Request Failed | Endpoint: %s | Error: %s", endpoint, re)
    except json.JSONDecodeError:
        logger.error("API Response not JSON decodable | Endpoint: %s", endpoint)
    except Exception as e:
        logger.exception("Unexpected error during API call | Endpoint: %s | Error: %s", endpoint, e)

    return None


# ============================================================
# API Wrappers
# ============================================================

def get_train_info(train_number: str) -> Optional[Dict[str, Any]]:
    """Fetch train information."""
    return call_api("trainInfo", method="GET", params={"trainNumber": train_number})


def check_pnr_status(pnr: str) -> Optional[Dict[str, Any]]:
    """Check PNR status."""
    return call_api("checkPNRStatus", method="GET", params={"pnr": pnr})


def live_at_station(station_code: str) -> Optional[Dict[str, Any]]:
    """Fetch live trains at a station."""
    return call_api("liveAtStation", method="GET", params={"stnCode": station_code})


def track_train(train_number: str, date_str: str) -> Optional[Dict[str, Any]]:
    """Track a train's live status by number and date."""
    return call_api("fetch-train-status", method="POST", payload={"trainNumber": train_number, "dates": date_str})


def search_train_between_stations(from_code: str, to_code: str) -> Optional[Dict[str, Any]]:
    """Search trains running between two stations."""
    return call_api(
        "searchTrainBetweenStations",
        method="POST",
        payload={"fromStnCode": from_code, "toStnCode": to_code},
    )


# ============================================================
# Kafka Consumer & Producer Logic
# ============================================================

def consume_and_produce():
    date_str_api = datetime.now().strftime("%d-%m-%Y")
    create_topic_if_not_exists(LIVE_STATUS_TOPIC, num_partitions=1, replication_factor=1)

    try:
        consumer = KafkaConsumer(
            CONSUME_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="train-numbers-consumer-group",
            value_deserializer=lambda x: x.decode("utf-8"),
        )

        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        )

        logger.info("Subscribed to topic: %s", CONSUME_TOPIC)

        executor = ThreadPoolExecutor(max_workers=10)
        lock = threading.Lock()

        def handle_api_result(train_number, future):
            try:
                live_status = future.result(timeout=35)
                if live_status:
                    normalized = normalize_api_response(live_status)
                    with lock:
                        if len(normalized) > 0:
                            producer.send(
                                LIVE_STATUS_TOPIC,
                                key=train_number.encode("utf-8"),
                                value=normalized
                            )
                            producer.flush()
                    logger.info("Produced live status for Train: %s", train_number)
                else:
                    logger.warning("No live status returned for Train: %s", train_number)
            except Exception as e:
                logger.exception("Error in API future for Train %s: %s", train_number, e)

        for message in consumer:
            train_number = message.value
            logger.info("Consumed message | Train Number: %s", train_number)
            future = executor.submit(track_train, train_number, date_str_api)
            future.add_done_callback(lambda fut, tn=train_number: handle_api_result(tn, fut))

    except KafkaError as ke:
        logger.exception("Kafka Consumer/Producer Error: %s", ke)
    except Exception as e:
        logger.exception("Unexpected error in consume_and_produce: %s", e)

# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    logger.info("Starting Train Status Service...")
    consume_and_produce()
