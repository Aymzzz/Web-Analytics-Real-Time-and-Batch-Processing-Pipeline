import os
import subprocess
from cassandra.cluster import Cluster
from datetime import datetime

# Cassandra settings
CASSANDRA_KEYSPACE = "web_analytics"
LOG_TABLE = "LOG"
RESULTS_TABLE = "RESULTS"  # Updated to match your existing table

def log_and_print(message):
    """Log and print a message."""
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

def check_new_logs():
    """Check if there are new logs to process."""
    session = connect_to_cassandra()
    today = datetime.now().strftime('%Y-%m-%d')

    # Fetch counts of logs and results for today
    log_query = f"SELECT COUNT(*) FROM {LOG_TABLE} WHERE date = %s"
    results_query = f"SELECT COUNT(*) FROM {RESULTS_TABLE} WHERE date = %s"

    log_count = session.execute(log_query, (today,)).one()[0]
    results_count = session.execute(results_query, (today,)).one()[0]

    log_and_print(f"Logs count for today: {log_count}")
    log_and_print(f"Results count for today: {results_count}")

    # Check if new logs exist
    return log_count > results_count

def run_in_terminal_tab(script_path, tab_name):
    """Run a script in a new terminal tab."""
    command = f"gnome-terminal --tab --title='{tab_name}' -- bash -c 'python3 {script_path}; exec bash'"
    subprocess.run(command, shell=True)

def run_real_time_pipeline():
    """Run the full real-time processing pipeline."""
    log_and_print("Starting the Real-Time Processing Pipeline...")

    # Open each script in a new tab
    run_in_terminal_tab("scripts/jmeter_alt.py", "Traffic Simulator (JMeter)")
    run_in_terminal_tab("scripts/producer_kafka.py", "Kafka Producer")
    run_in_terminal_tab("scripts/consumer_kafka.py", "Kafka Consumer")
    run_in_terminal_tab("scripts/real_time_processing.py", "Real-Time Processing")

    # Wait for user to stop real-time processing
    input("\nPress Enter to stop the Real-Time Processing Pipeline...")

    log_and_print("Real-Time Processing Pipeline stopped.")

    # Ask if the user wants to run batch processing
    run_batch = input("\nDo you want to run Batch Processing now? (y/n): ").strip().lower()
    if run_batch == "y":
        if check_new_logs():
            run_batch_processing()
        else:
            print("No new logs to process for Batch Processing.")

def run_batch_processing():
    """Run batch processing in a new terminal tab."""
    log_and_print("Starting Batch Processing...")
    run_in_terminal_tab("scripts/batch_processing.py", "Batch Processing")

def view_results_table():
    """Display the current contents of the RESULTS table."""
    log_and_print("Fetching current results from Cassandra...")
    session = connect_to_cassandra()

    try:
        query = f"SELECT * FROM {RESULTS_TABLE} LIMIT 20"
        rows = session.execute(query)

        print("\nCurrent contents of the RESULTS table:")
        print("-" * 70)
        print(f"{'DATE':<15} {'PAGE_URL':<20} {'VISITS':<10} {'LAST_PROCESSED':<30}")
        print("-" * 70)
        for row in rows:
            print(f"{row.date:<15} {row.page_url:<20} {row.visits:<10} {row.last_processed}")
        print("-" * 70)
    except Exception as e:
        log_and_print(f"Error fetching RESULTS table: {e}")

def prompt_user():
    """Prompt the user for actions."""
    print("\nChoose an option:")
    print("1. Run Real-Time Processing Pipeline")
    print("2. Run Batch Processing")
    print("3. Exit")
    print("4. View RESULTS Table")

    choice = input("Enter your choice (1/2/3/4): ").strip()
    if choice not in {"1", "2", "3", "4"}:
        print("Invalid choice. Please try again.")
        return prompt_user()
    return choice

def main():
    """Main pipeline management script."""
    while True:
        choice = prompt_user()

        if choice == "1":
            run_real_time_pipeline()

        elif choice == "2":
            if check_new_logs():
                run_batch_processing()
            else:
                print("No new logs to process for Batch Processing.")

        elif choice == "3":
            print("Exiting pipeline...")
            break

        elif choice == "4":
            view_results_table()

if __name__ == "__main__":
    main()
