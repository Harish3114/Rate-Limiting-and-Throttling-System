import requests
import time
import random

API_URL = "http://127.0.0.1:8000/api"

# Define users with friendly names
USERS = {
    "key_123": "Hari",
    "key_456": "Rajuu",
    "user_1": "Mike",
    "user_2": "Lara",
    "user_3": "Joe",
}

# Function to simulate requests for a single user
def simulate_user(api_key, total_requests, delay=0.5):
    for i in range(total_requests):
        try:
            response = requests.get(API_URL, params={"api_key": api_key})
            data = response.json()
            print(f"[{USERS.get(api_key, api_key)}] Attempt {i+1}: {data['status']} - {data['message']}")
        except Exception as e:
            print(f"[{USERS.get(api_key, api_key)}] Error: {e}")
        time.sleep(delay)

if __name__ == "__main__":
    # Simulate each user with random request counts and delays
    for api_key in USERS.keys():
        total_requests = random.randint(5, 12)   # Random requests per user
        delay = random.uniform(0.3, 1.0)        # Random delay between requests
        simulate_user(api_key, total_requests, delay)
