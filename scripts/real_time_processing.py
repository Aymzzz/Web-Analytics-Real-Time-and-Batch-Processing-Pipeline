from confluent_kafka import Consumer, KafkaException, KafkaError
from cassandra.cluster import Cluster
from collections import Counter
from datetime import datetime
import json
import logging
import argparse

# Configure logging
logging.basicConfig(
    filename="logs/stream_processing.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

KAFKA_BROKER = "localhost:9092"
RAWLOG_TOPIC = "RAWLOG"
CASSANDRA_KEYSPACE = "web_analytics"
RESULTS_TABLE = "RESULTS"

def log_and_print(message):
    """Log and print a message."""
    logging.info(message)
    print(message)

def connect_to_cassandra():
    """Establish a connection to the Cassandra database."""
    try:
        log_and_print("Connecting to Cassandra...")
        cluster = Cluster(['127.0.0.1'])
        session = cluster.connect()
        session.set_keyspace(CASSANDRA_KEYSPACE)
        return session
    except Exception as e:
        log_and_print(f"Error connecting to Cassandra: {e}")
        raise

def create_consumer(group_id):
    """Create a Kafka consumer for the RAWLOG topic."""
    return Consumer({
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    })

def update_cumulative_visits(cassandra_session, page_visits):
    """Update cumulative visits in the RESULTS table."""
    for uri, new_visits in page_visits.items():
        try:
            
            current_visits = 0
            query = f"""
            SELECT visits FROM {RESULTS_TABLE} WHERE date = %s AND page_url = %s
            """
            rows = cassandra_session.execute(query, (datetime.now().strftime('%Y-%m-%d'), uri))
            for row in rows:
                current_visits = row.visits

            total_visits = current_visits + new_visits

            cassandra_session.execute(
                f"""
                INSERT INTO {RESULTS_TABLE} (date, page_url, visits, last_processed)
                VALUES (%s, %s, %s, %s)
                """,
                (datetime.now().strftime('%Y-%m-%d'), uri, total_visits, datetime.utcnow())
            )
            log_and_print(f"Updated: {uri} - Total visits: {total_visits}")
        except Exception as e:
            log_and_print(f"Error updating cumulative visits for {uri}: {e}")

def process_logs(consumer, cassandra_session, interval):
    """Consume logs from Kafka, aggregate, and update results in Cassandra."""
    log_and_print(f"Starting stream processing with INTERVAL={interval}s...")
    consumer.subscribe([RAWLOG_TOPIC])
    page_visits = Counter()

    try:
        while True:
            messages = consumer.consume(timeout=interval)
            if not messages:
                log_and_print("No messages received in this interval.")
                continue

            for msg in messages:
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        log_and_print(f"Consumer error: {msg.error()}")
                        raise KafkaException(msg.error())

                # Parse message
                try:
                    log_entry = json.loads(msg.value().decode('utf-8'))
                    log_and_print(f"Consumed message: {log_entry}")

                    request_uri = log_entry.get('request_uri')
                    if request_uri:
                        page_visits[request_uri] += 1
                except json.JSONDecodeError as e:
                    log_and_print(f"Failed to decode message: {e}")
                except Exception as e:
                    log_and_print(f"Error processing message: {e}")

            update_cumulative_visits(cassandra_session, page_visits)

            page_visits.clear()

    except KeyboardInterrupt:
        log_and_print("Shutting down stream processing...")
    finally:
        consumer.close()

def main():
    parser = argparse.ArgumentParser(description="Real-Time Stream Processing for Access Logs")
    parser.add_argument("--interval", type=int, default=300, help="Processing interval in seconds (default: 300)")
    parser.add_argument("--group_id", type=str, default="stream-processing-group", help="Kafka consumer group ID")
    args = parser.parse_args()

    session = connect_to_cassandra()
    consumer = create_consumer(args.group_id)

    process_logs(consumer, session, args.interval)

if __name__ == "__main__":
    main()
