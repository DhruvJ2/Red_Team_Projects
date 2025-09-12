import requests
import argparse
import pyfiglet
import threading

asciiBanner = pyfiglet.figlet_format("Recursive Directory Brute Force")
print(asciiBanner)

parser = argparse.ArgumentParser(description="Recursive threaded directory brute force tool")
parser.add_argument('-u', '--url', help='Enter URL to brute force', default='http://testhtml5.vulnweb.com')
parser.add_argument('-w', '--wordlist', help='Enter wordlist', default='./common.txt')
args = parser.parse_args()

with open(args.wordlist, 'r') as f:
    wordlist = f.read().splitlines()

MAX_THREADS = 10
# limits maximum concurrent threads globally to avoid too many threads
thread_limiter = threading.BoundedSemaphore(MAX_THREADS)

def check_directory(base_url, directory):
    url = base_url.rstrip('/') + '/' + directory
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f'[+] Found Directory: {url}')
            # Recursively check subdirectories inside this directory
            for subdir in wordlist:
                thread_limiter.acquire()
                t = threading.Thread(target=check_directory, args=(url, subdir))
                t.start()
                t.join(0)  # Let thread run without waiting here
                thread_limiter.release()
    except requests.RequestException:
        pass

# Start scanning from base URL
for directory in wordlist:
    thread_limiter.acquire()
    thread = threading.Thread(target=check_directory, args=(args.url, directory))
    thread.start()
    thread.join(0)
    thread_limiter.release()
