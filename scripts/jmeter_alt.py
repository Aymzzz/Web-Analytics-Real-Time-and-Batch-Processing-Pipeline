import requests
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TrafficSimulator:
    def __init__(self, base_url='http://localhost', total_requests=5500, duration=300):
        """
        Initialize Traffic Simulator

        :param base_url: Base URL of the load balancer
        :param total_requests: Total number of requests to simulate
        :param duration: Total duration of simulation in seconds
        """
        self.base_url = base_url
        self.total_requests = total_requests
        self.duration = duration

        # This is to simulate the traffic based on the project's specification.
        self.traffic_distribution = {
            '/product1': 0.50,  # 50%
            '/product2': 0.25,  # 25%
            '/product3': 0.15,  # 15%
            '/product4': 0.08,  #  8%
            '/product5': 0.02,  #  2%
        }

        assert round(sum(self.traffic_distribution.values()), 2) == 1.0, "Traffic distribution must sum to 1.0" #validating the distribution

        self.results = {endpoint: 0 for endpoint in self.traffic_distribution.keys()}
        self.errors = {endpoint: 0 for endpoint in self.traffic_distribution.keys()}
        self.lock = threading.Lock()
        self.progress_bar = tqdm(total=self.total_requests, desc="Simulating Traffic")

    def send_request(self, endpoint):
        """
        Send a single request to the specified endpoint

        :param endpoint: Endpoint to request
        :return: Success status
        """
        try:
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers={"X-Date": time.strftime("%Y-%m-%d")},
                timeout=5
            )

            return response.status_code == 200
        except Exception as e:
            logging.error(f"Error requesting {endpoint}: {e}")
            return False

    def worker(self):
        """
        Worker method to generate traffic according to distribution
        """
        start_time = time.time()
        end_time = start_time + self.duration

        while time.time() < end_time:
            endpoint = random.choices(
                list(self.traffic_distribution.keys()),
                weights=list(self.traffic_distribution.values())
            )[0]

            # Send request
            success = self.send_request(endpoint)

            # Track results
            with self.lock:
                if success:
                    self.results[endpoint] += 1
                else:
                    self.errors[endpoint] += 1
                self.progress_bar.update(1)

            sleep_time = random.uniform(0.1, 1.0)  # Sleep between 0.1 to 1.0 seconds
            time.sleep(sleep_time)

    def run(self, num_threads=10):
        """
        Run the traffic simulation

        :param num_threads: Number of concurrent threads to simulate traffic
        """
        logging.info("Starting Traffic Simulation...")
        logging.info(f"Total Requests: {self.total_requests}")
        logging.info(f"Duration: {self.duration} seconds")
        logging.info(f"Threads: {num_threads}")
        logging.info("\nTraffic Distribution:")
        for endpoint, percentage in self.traffic_distribution.items():
            logging.info(f"{endpoint}: {percentage * 100}%")

        # Use ThreadPoolExecutor for concurrent requests
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit workers
            futures = [
                executor.submit(self.worker)
                for _ in range(num_threads)
            ]

            # Wait for all to complete
            for future in futures:
                future.result()

        # Print results
        logging.info("\n--- Simulation Results ---")
        total_successful = sum(self.results.values())
        total_errors = sum(self.errors.values())

        logging.info("\nSuccessful Requests:")
        for endpoint, count in self.results.items():
            percentage = (count / total_successful) * 100 if total_successful > 0 else 0
            logging.info(f"{endpoint}: {count} ({percentage:.2f}%)")

        logging.info("\nError Requests:")
        for endpoint, count in self.errors.items():
            logging.info(f"{endpoint}: {count}")

        logging.info(f"\nTotal Successful Requests: {total_successful}")
        logging.info(f"Total Error Requests: {total_errors}")
        self.progress_bar.close()

if __name__ == "__main__":
    simulator = TrafficSimulator(
        total_requests=5500,
        duration=300  # 5 minutes
    )
    simulator.run(num_threads=20)
