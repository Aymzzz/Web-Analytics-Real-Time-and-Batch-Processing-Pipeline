from kafka import KafkaProducer
import json
import time
import logging
import subprocess

# Configure logging
logging.basicConfig(
    filename="logs/kafka_producer.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

KAFKA_TOPIC = "RAWLOG"
KAFKA_BROKER = "localhost:9092"
NGINX_LOG_PATH = "/var/log/nginx/access.log"
NGINX_LOG_PATHS = [
    "/var/log/nginx/backend-1-access.log",
    "/var/log/nginx/backend-2-access.log",
    "/var/log/nginx/backend-3-access.log",
]


def log_and_print(message):
    logging.info(message)
    print(message)

def send_to_kafka(producer, topic, log_entry):
    """Send a single log entry to Kafka."""
    try:
        producer.send(topic, value=log_entry)
        log_and_print(f"Sent log: {log_entry}")
    except Exception as e:
        log_and_print(f"Error sending log: {e}")

def read_nginx_logs():
    """Read NGINX logs with sudo and return the lines."""
    try:
        result = subprocess.run(['sudo', 'cat', NGINX_LOG_PATH], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            log_and_print(f"Error reading log file: {result.stderr.decode()}")
            return []
        return result.stdout.decode().splitlines()
    except Exception as e:
        log_and_print(f"Unexpected error reading log file: {e}")
        return []

def main():
    producers = [
        KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )
        for _ in NGINX_LOG_PATHS
    ]

    log_and_print(f"Monitoring logs: {', '.join(NGINX_LOG_PATHS)}")
    
    # Open all log files in tail mode
    log_files = [open(path, 'r') for path in NGINX_LOG_PATHS]
    for log_file in log_files:
        log_file.seek(0, 2)

    while True:
        for i, log_file in enumerate(log_files):
            line = log_file.readline()
            if not line:
                time.sleep(1)
                continue
            try:
                log_entry = json.loads(line.strip())
                send_to_kafka(producers[i], KAFKA_TOPIC, log_entry)
            except json.JSONDecodeError as e:
                log_and_print(f"Invalid log line: {line.strip()} - Error: {e}")


if __name__ == "__main__":
    main()
