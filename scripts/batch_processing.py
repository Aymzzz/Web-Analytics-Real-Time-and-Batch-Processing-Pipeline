from cassandra.cluster import Cluster
import logging
from collections import defaultdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename="logs/batch_processing.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

CASSANDRA_KEYSPACE = "web_analytics"
LOG_TABLE = "LOG"
RESULTS_TABLE = "RESULTS"
TOP_N = 3  # Number of top pages to analyze

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

def fetch_existing_results(session):
    """Fetch current visit counts from the RESULTS table."""
    log_and_print("Fetching existing results from the RESULTS table...")
    query = f"SELECT date, page_url, visits FROM {RESULTS_TABLE}"
    rows = session.execute(query)
    results = defaultdict(int)
    for row in rows:
        results[(row.date, row.page_url)] += row.visits
    log_and_print(f"Fetched {len(results)} existing results.")
    return results

def fetch_new_logs(session):
    """Fetch all logs from the LOG table."""
    log_and_print("Fetching logs from the LOG table...")
    query = f"SELECT date, request_uri FROM {LOG_TABLE}"
    rows = session.execute(query)
    logs = defaultdict(list)
    for row in rows:
        logs[row.date].append(row.request_uri)
    log_and_print(f"Fetched logs for {len(logs)} dates.")
    return logs

def aggregate_results(existing_results, new_logs):
    """Aggregate visit counts by combining new logs with existing results."""
    log_and_print("Aggregating results...")
    aggregated_results = defaultdict(int)

    # Add existing results
    for (log_date, uri), count in existing_results.items():
        aggregated_results[(log_date, uri)] += count

    # Add counts from new logs
    for log_date, uris in new_logs.items():
        for uri in uris:
            aggregated_results[(log_date, uri)] += 1

    log_and_print(f"Aggregated results for {len(aggregated_results)} page-date combinations.")
    return aggregated_results

def store_results(session, aggregated_results):
    """Store aggregated results in the RESULTS table."""
    log_and_print("Storing aggregated results in Cassandra...")
    session.execute(f"TRUNCATE {RESULTS_TABLE}")  # Clear previous results
    for (log_date, uri), visits in aggregated_results.items():
        session.execute(
            f"""
            INSERT INTO {RESULTS_TABLE} (date, page_url, visits, last_processed)
            VALUES (%s, %s, %s, %s)
            """,
            (log_date, uri, visits, datetime.utcnow())
        )
        log_and_print(f"Stored result: {uri} with {visits} visits for date {log_date}")

def process_all_logs():
    """Process all logs and update the RESULTS table."""
    session = connect_to_cassandra()

    existing_results = fetch_existing_results(session)
    new_logs = fetch_new_logs(session)
    aggregated_results = aggregate_results(existing_results, new_logs)
    store_results(session, aggregated_results)

    log_and_print("Batch processing completed successfully.")

if __name__ == "__main__":
    process_all_logs()
