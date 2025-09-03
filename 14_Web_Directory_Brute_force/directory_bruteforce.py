import requests
import argparse, pyfiglet
import threading

asciiBanner = pyfiglet.figlet_format("Directory Brute Force")
print(asciiBanner)

parser = argparse.ArgumentParser(description="Simple directory brute force tool")
parser.add_argument('-u', '--url', help='Enter url to brute force', default='http://testhtml5.vulnweb.com')
parser.add_argument('-w', '--wordlist', help='Enter wordlist', default='./common.txt')
args = parser.parse_args()

directoryPath = args.wordlist

with open(directoryPath, 'r') as f:
    wordlist = f.read().splitlines()

def check_directory(directory):
    directoryUrl = args.url.rstrip('/') + '/' + directory
    try:
        response = requests.get(directoryUrl)
        if response.status_code == 200:
            print(f'[+] Found Directory: {directoryUrl}')
    except requests.RequestException as e:
        pass

## Multi-Threading
threads = []
max_threads = 5 

for directory in wordlist:
    while threading.active_count() > max_threads:
        pass  # Wait for threads to finish
    t = threading.Thread(target=check_directory, args=(directory,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
