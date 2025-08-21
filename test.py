import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import requests
import re
# from kafka import KafkaConsumer, KafkaProducer
# from kafka.admin import KafkaAdminClient, NewTopic
# from kafka.errors import KafkaError, TopicAlreadyExistsError

# ============================================================
# Logging Configuration
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("Testing API Response")

BASE_URL = "https://easy-rail.onrender.com/fetch-train-status"


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


def track_train(train_number: str, date_str: str):
    if not train_number or not isinstance(train_number, str) or len(train_number) != 5:
        return {"success": False, "error": "Invalid train number. It must be a 5-character string."}

    if not re.match(r"^\d{2}-\d{2}-\d{4}$", date_str):
        return {"success": False, "error": "Invalid date format. Please use dd-mm-yyyy format."}

    try:
        parsed_date = datetime.strptime(date_str, "%d-%m-%Y")
        if parsed_date.strftime("%d-%m-%Y") != date_str:
            raise ValueError
    except ValueError:
        return {"success": False, "error": "Invalid date. Please check the day, month, and year values."}

    url = "https://easy-rail.onrender.com/fetch-train-status"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    payload = {"trainNumber": train_number, "dates": [date_str, "18-08-2025"]}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return {"data": normalize_api_response(data)}
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}



if __name__ == "__main__":
    date_str_api = datetime.now().strftime("%d-%m-%Y")
    live_status = track_train("56142", date_str_api)

    print(live_status)