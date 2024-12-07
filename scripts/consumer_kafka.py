from kafka import KafkaConsumer
from cassandra.cluster import Cluster
import json
import logging

logging.basicConfig(
    filename="logs/kafka_consumer.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

KAFKA_TOPIC = "RAWLOG"
KAFKA_BROKER = "localhost:9092"
CASSANDRA_KEYSPACE = "web_analytics"
CASSANDRA_TABLE = "LOG"

def log_and_print(message):
    """Log and print a message."""
    logging.info(message)
    print(message)

def connect_to_cassandra():
    """Establish a connection to the Cassandra database."""
    log_and_print("Connecting to Cassandra...")
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect()
    session.set_keyspace(CASSANDRA_KEYSPACE)
    return session

def clear_cassandra_table(session):
    """Clear the Cassandra table."""
    log_and_print(f"Clearing the Cassandra table: {CASSANDRA_TABLE}")
    session.execute(f"TRUNCATE {CASSANDRA_TABLE};")
    log_and_print("Cassandra table cleared.")

def sanitize_log_entry(log_entry):
    """Sanitize log entry to replace empty strings with None."""
    return {key: (value if value != "" else None) for key, value in log_entry.items()}

def consume_and_store():
    """Consume messages from Kafka and store them in Cassandra."""
    log_and_print(f"Subscribing to Kafka topic: {KAFKA_TOPIC}")
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=10000  # Exit after 10 seconds of no messages
    )
    session = connect_to_cassandra()

    clear_cassandra_table(session)

    for message in consumer:
        raw_log_entry = message.value
        sanitized_log_entry = sanitize_log_entry(raw_log_entry)

        log_and_print(f"Consumed message from Kafka: {raw_log_entry}")
        log_and_print(f"Sanitized log entry: {sanitized_log_entry}")

        try:
            date = sanitized_log_entry['timestamp'].split('T')[0]

            session.execute(
                f"""
                INSERT INTO {CASSANDRA_TABLE} (
                    date, timestamp, remote_addr, request_method, request_uri,
                    status, body_bytes_sent, request_time, http_referrer, http_user_agent
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    date, sanitized_log_entry['timestamp'], sanitized_log_entry['remote_addr'],
                    sanitized_log_entry['request_method'], sanitized_log_entry['request_uri'],
                    sanitized_log_entry['status'], sanitized_log_entry['body_bytes_sent'],
                    sanitized_log_entry['request_time'], sanitized_log_entry['http_referrer'],
                    sanitized_log_entry['http_user_agent']
                )
            )
            log_and_print(f"Inserted into Cassandra: {sanitized_log_entry}")
        except Exception as e:
            log_and_print(f"Error inserting into Cassandra: {e}")

    log_and_print("Kafka consumer finished processing messages.")

if __name__ == "__main__":
    consume_and_store()
