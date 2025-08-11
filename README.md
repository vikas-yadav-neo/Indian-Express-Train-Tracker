# **Indian Express Train Tracker**

Overview
---
* Setting up the environment
* Getting source data (live or near real-time train running status)
* A clear folder structure and commands
* Processing with PySpark (batch & streaming)
* Recommended Superset visualizations


## Indian Express Train Tracker — Setup, Data Processing (PySpark) & Superset Visualizations
A step-by-step guide to create a reproducible project that fetches Indian Express train running data, processes it using PySpark (batch or streaming), and visualizes insights on Apache Superset.

## Architecture Overview

```plaintext
Input Data (API / File / Stream)
        │
        ▼
Read Source Using Spark
        │
        ▼
Write Raw Data into HDFS
        │
        ▼
Process Data in Spark
        │
        ▼
Write Processed Data into PostgreSQL
        │
        ▼
View on Superset Dashboard
```

## 1. Overview

This project will:
- Fetch train running status data from Indian Railways API (or free alternatives)
- Store raw data in local filesystem / HDFS
- Process the data in PySpark (e.g., delay analysis, route coverage, performance stats)
- Load processed data into PostgreSQL / Hive
- Build dashboards in Apache Superset for monitoring


## 2. Architecture

Indian Railways API / Scraper → Raw JSON/CSV → Spark Jobs → Processed Parquet / PostgreSQL → Apache Superset


## 3. Prerequisites

**Required Tools:**
- Python 3.9+
- Java 11+
- Apache Spark 3.x
- Docker & Docker Compose
- Git
- PostgreSQL (for Superset datasource)
- Apache Superset

**Optional Tools:**
- HDFS / MinIO for data lake storage
- Airflow for scheduling

**APIs / Data Sources:**
- [Railway API (paid & free plans)](https://railwayapi.com/)
- [Indian Railways NTES API (unofficial, scrape-based)](https://enquiry.indianrail.gov.in/ntes/)
- Mock datasets for testing

## 4. Repository Layout

```plaintext
indian-express-tracker/
│
├── infra/                 # Docker, Spark, Superset setup
├── data/
│   ├── raw/               # Raw JSON/CSV data from API
│   ├── processed/         # Processed Parquet data
├── notebooks/             # Jupyter Notebooks for exploration
├── pyspark_jobs/
│   ├── batch/             # Batch jobs for daily aggregates
│   ├── streaming/         # Streaming jobs for near real-time tracking
├── superset/
│   ├── dashboards/        # JSON exports of Superset dashboards
│   ├── charts/            # Chart config files
├── scripts/
│   ├── fetch_data.py      # Calls API and stores raw data
│   ├── process_data.py    # Local/Spark processing script
├── dags/                  # Airflow DAGs (if used)
└── README.md
```

---

## 5. Environment Setup

### 5.1 Python Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install requests pandas pyspark pyarrow fastparquet sqlalchemy psycopg2-binary
```

### 5.2 Docker Compose (Spark + PostgreSQL + Superset)

Create `docker-compose.yml` with:

* Spark Master & Worker
* PostgreSQL
* Superset
* (Optional) HDFS

Start services:

```bash
docker compose up -d
```

---

## 6. Getting Source Data

### Option 1 — Railway API (Preferred)

Register at [https://railwayapi.com](https://railwayapi.com)
Get API key and test:

```python
import requests

API_KEY = "your_api_key"
TRAIN_NO = "12951"  # Example: Mumbai Rajdhani
url = f"https://api.railwayapi.com/v2/live/train/{TRAIN_NO}/date/12-08-2025/apikey/{API_KEY}/"

response = requests.get(url)
data = response.json()
print(data)
```

### Option 2 — Web Scraping (Unofficial)

Use `BeautifulSoup` & `requests` to scrape NTES (may require CAPTCHA handling).

### Option 3 — Static Dataset (Development)

Download mock CSV datasets for testing.

---

## 7. Data Processing with Spark

### 7.1 Batch Job Example

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, datediff

spark = SparkSession.builder.appName("TrainBatchProcessing").getOrCreate()

df = spark.read.json("data/raw/*.json")

# Convert timestamps & calculate delays
df = df.withColumn("scheduled_arrival", to_timestamp(col("sch_arrival")))
df = df.withColumn("actual_arrival", to_timestamp(col("act_arrival")))
df = df.withColumn("delay_minutes", (col("actual_arrival").cast("long") - col("scheduled_arrival").cast("long")) / 60)

df.write.mode("overwrite").parquet("data/processed/train_delays")
```

### 7.2 Streaming Job Example (Near Real-Time)

```python
stream_df = spark \
    .readStream \
    .schema(schema) \
    .json("data/raw/streaming/")

processed_df = stream_df.withColumn("delay_minutes", ...)

query = processed_df.writeStream \
    .outputMode("append") \
    .format("parquet") \
    .option("path", "data/processed/streaming") \
    .option("checkpointLocation", "data/checkpoints") \
    .start()

query.awaitTermination()
```

---

## 8. Loading Data into Superset

* Create a PostgreSQL table:

```sql
CREATE TABLE train_delays AS SELECT * FROM parquet_scan('data/processed/train_delays');
```

* In Superset, add PostgreSQL connection.
* Import table and create charts.

---

## 9. Superset Visualizations

Recommended dashboards:

1. **Train Delay Leaderboard** — Top delayed trains (avg delay in minutes).
2. **On-Time Performance %** — % of trains arriving on time per day/week.
3. **Delay Heatmap** — Delay by route & time of day.
4. **Route Performance Map** — Geo map of train routes with color-coded delays.
5. **Top 5 Most Delayed Routes** — Aggregated stats.
6. **Real-Time Train Tracker** — Current running trains with status.
7. **Delay Trend Chart** — Delay trend over time for selected train.
8. **Comparison Chart** — Compare delays of multiple trains.
9. **Station Bottlenecks** — Stations causing most delays.

---

## 10. Next Steps

* Automate API fetch with Airflow or cron
* Add anomaly detection for unusual delays
* Integrate weather data to correlate with train delays
* Deploy to cloud with S3 + EMR + Superset

---

## Reference Links
* [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
* [Apache Superset Documentation](https://superset.apache.org/docs/intro)
* [Apache Airflow Documentation](https://airflow.apache.org/docs/)
* [Railway API Docs](https://railwayapi.com/api)
* [HDFS Overview](https://hadoop.apache.org/docs/r1.2.1/hdfs_design.html)
* [PostgreSQL Documentation](https://www.postgresql.org/docs/)
* [Live Train Status Postman Collection](https://www.postman.com/postman/published-postman-templates/documentation/ch6hswr/live-train-status)
* [IRCTC Connect Main GitHub](https://github.com/yogeshft/irctc-connect-main)
* [Indian Railways NTES](https://enquiry.indianrail.gov.in/ntes/)
