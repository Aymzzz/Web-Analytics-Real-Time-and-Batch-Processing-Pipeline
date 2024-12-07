import subprocess
import time
import os

# Constants
ZOOKEEPER_SERVICE = 'zookeeper.service'
KAFKA_SERVICE = 'kafka.service'
KAFKA_HOME = os.path.expanduser('/usr/local/kafka')
PROJECT_TOPICS = {
    "RAWLOG": {"replication_factor": 1, "partitions": 3},
    "RESULTS": {"replication_factor": 1, "partitions": 1},
    "AGGREGATED_LOGS": {"replication_factor": 1, "partitions":1}
}

def start_service(service_name):
    """Start a systemctl service."""
    output = subprocess.run(["systemctl", "status", service_name], capture_output=True)
    status = output.stdout.decode().strip()
    if "inactive" in status:
        print(f"Starting {service_name}...")
        subprocess.run(["sudo", "systemctl", "start", service_name])
        time.sleep(5)
    else:
        print(f"{service_name} is already running.")

def start_kafka_server(server_id):
    """Start a Kafka broker in a new terminal."""
    print(f"Starting Kafka broker {server_id}...")
    server_file = f"{KAFKA_HOME}/config/server-{server_id}.properties"
    if not os.path.exists(server_file):
        print(f"Error: Kafka server configuration file '{server_file}' not found.")
        return
    subprocess.Popen(["gnome-terminal", "--tab", "--title", f'Kafka Broker {server_id}', "--", "bash", "-c",
                      f"{KAFKA_HOME}/bin/kafka-server-start.sh {server_file}; exec bash"])
    time.sleep(5)

def create_topic(topic_name, replication_factor, partitions):
    """Create a Kafka topic with specified settings."""
    print(f"Creating topic '{topic_name}' with {partitions} partitions and replication factor {replication_factor}...")
    result = subprocess.run([f"{KAFKA_HOME}/bin/kafka-topics.sh",
                             "--create",
                             "--bootstrap-server", "localhost:9092",
                             "--replication-factor", str(replication_factor),
                             "--partitions", str(partitions),
                             "--topic", topic_name],
                            capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Topic '{topic_name}' created successfully.")
    else:
        print(f"Error creating topic '{topic_name}': {result.stderr}")

def list_topics():
    """List all available Kafka topics."""
    print("Listing all available topics...")
    result = subprocess.run([f"{KAFKA_HOME}/bin/kafka-topics.sh",
                             "--list",
                             "--bootstrap-server", "localhost:9092"],
                            capture_output=True, text=True)

    if result.returncode == 0:
        topics = result.stdout.strip().split('\n')
        if topics:
            print("Available topics:")
            for topic in topics:
                print(f"- {topic}")
        else:
            print("No topics available.")
    else:
        print(f"Error listing topics: {result.stderr}")

def main():
    print("Starting Kafka setup for the project...")
    start_service(ZOOKEEPER_SERVICE)
    start_service(KAFKA_SERVICE)

    for broker_id in range(3):
        start_kafka_server(broker_id)

    print("\nCreating project-specific Kafka topics...")
    for topic_name, settings in PROJECT_TOPICS.items():
        create_topic(topic_name, settings["replication_factor"], settings["partitions"])

    print("\nListing all Kafka topics after creation:")
    list_topics()

    print("\nKafka setup completed.")

if __name__ == "__main__":
    main()
