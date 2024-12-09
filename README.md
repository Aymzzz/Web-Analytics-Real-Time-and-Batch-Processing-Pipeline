# Web Analytics Real-Time and Batch Processing Pipeline

This project implements a **real-time web analytics processing pipeline** using **Kafka** for messaging, **Cassandra** for storage, and **Python** for processing the logs. The pipeline aggregates page visit data from raw logs in real time and batch processes older logs periodically, while ensuring no data is lost or overwritten.

## Project Overview

The project consists of two major components:

1. **Real-Time Processing Pipeline**:  
   - **Kafka Producer** to simulate and produce web logs.
   - **Kafka Consumer** to consume raw logs and store them in the `LOG` table in **Cassandra**.
   - **Real-Time Analytics** to calculate the most visited pages (top N) and store the results in the `RESULTS` table in **Cassandra**.

2. **Batch Processing Pipeline**:  
   - Periodic batch jobs to aggregate all logs from the `LOG` table and update the `RESULTS` table with the top N most visited pages.
   - Ensures that the results table is up-to-date even if real-time processing hasn't been running.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Pipeline](#running-the-pipeline)
  - [Real-Time Pipeline](#real-time-pipeline)
  - [Batch Processing](#batch-processing)
- [How It Works](#how-it-works)
  - [Real-Time Processing](#real-time-processing)
  - [Batch Processing](#batch-processing)
- [Monitoring Results](#monitoring-results)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Installation

### Prerequisites

Before setting up the project, ensure the following software is installed:

1. **Kafka** - For managing real-time log streams.
2. **Cassandra** - For storing raw logs and processed results.
3. **Python 3.x** - For running the scripts.
4. **pip** - For managing Python dependencies.

### Install Dependencies

First, clone the repository:

```bash
git clone <your-repo-url>
cd project-root
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Ensure Kafka and Cassandra are running and properly configured. If you're using Docker, there are pre-configured `docker-compose.yml` files available for easy setup.

---

## Configuration

### Kafka

Kafka is used to handle the real-time log streams.

1. Ensure Kafka is properly configured and running. If not, follow [Kafka Setup](https://kafka.apache.org/quickstart).
2. The main Kafka topic used is `RAWLOG`, which handles the raw logs. The output topic for results is `RESULTS`.

### Cassandra

1. Ensure Cassandra is running and properly configured.
2. The **web_analytics** keyspace and **LOG** and **RESULTS** tables should be created.

```sql
CREATE KEYSPACE web_analytics WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
```

3. **LOG** Table Structure:
```sql
CREATE TABLE LOG (
    date text,
    timestamp timestamp,
    request_uri text,
    status int,
    body_bytes_sent int,
    request_time double,
    http_referrer text,
    http_user_agent text,
    PRIMARY KEY (date, request_uri)
);
```

4. **RESULTS** Table Structure:
```sql
CREATE TABLE RESULTS (
    date text,
    page_url text,
    visits int,
    last_processed timestamp,
    PRIMARY KEY (date, page_url)
);
```

---

## Running the Pipeline

### Real-Time Pipeline

The real-time pipeline runs the following components:

1. **JMeter Alt (Traffic Simulator)**: Simulates web traffic by making requests to product pages.
2. **Kafka Producer**: Produces simulated log data to Kafka's `RAWLOG` topic.
3. **Kafka Consumer**: Consumes the logs from the `RAWLOG` topic and stores them in the `LOG` table in Cassandra.
4. **Real-Time Processing**: Aggregates the most visited pages every specified time interval (e.g., 5 minutes) and stores the results in the `RESULTS` table.

Run the entire pipeline (simulator, producer, consumer, and real-time processing) by executing the following:

```bash
python3 scripts/run.py
```

### Batch Processing

Batch processing is used to process logs that have already been consumed into the system. It aggregates the logs and stores the top N pages per day into the `RESULTS` table in Cassandra.

You can choose to run batch processing independently after the real-time pipeline has completed.

To run the batch processing:

1. **Run the Batch Processing Script**:  
   ```bash
   python3 scripts/batch_processing.py
   ```

2. The script will aggregate logs in the `LOG` table and update the `RESULTS` table with the top N pages based on the latest logs.

---

## How It Works

### Real-Time Processing

1. **Producer**: The producer script sends simulated logs to the `RAWLOG` Kafka topic.
2. **Consumer**: The Kafka consumer listens for incoming messages in the `RAWLOG` topic, processes them, and stores them in the `LOG` table in Cassandra.
3. **Analytics**: The `real_time_processing.py` script runs periodically, aggregating the top N most visited pages and updating the `RESULTS` table in Cassandra with this data.

### Batch Processing

1. **Fetch Logs**: Batch processing queries the `LOG` table for all logs, starting from the earliest.
2. **Aggregate Visits**: It calculates the top N most visited pages.
3. **Store Results**: The results are inserted into the `RESULTS` table, ensuring the `VISITS` count is updated.

---

## Monitoring Results

After running the pipeline, you can monitor the results of both real-time and batch processing by querying the `RESULTS` table:

```bash
cqlsh> SELECT * FROM web_analytics.RESULTS;
```

This will show the top N most visited pages for each date, with the `last_processed` timestamp indicating when the data was updated.

---

## Troubleshooting

### Kafka Consumer Issues

- **No Messages**: If no logs appear in the consumer, verify Kafka is properly running and the `RAWLOG` topic has messages. You can use the Kafka console consumer to check for messages:
  ```bash
  /usr/local/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic RAWLOG --from-beginning
  ```

- **Consumer Lag**: Ensure your Kafka consumer has the appropriate `group.id` to prevent it from missing messages.

### Cassandra Issues

- **Connection Issues**: If you cannot connect to Cassandra, ensure the Cassandra service is running and accessible.

- **Missing Tables**: If the `LOG` or `RESULTS` tables are missing, use the provided `cql` scripts to create them.

---
## **Notes for Future Development**
- This pipeline is scalable by adding more consumers and producers.
- The batch processing logic can be extended to support different aggregation types (e.g., hourly, weekly).
