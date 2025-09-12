import socket
import threading
from queue import Queue
import nmap  # For advanced service detection (requires 'python-nmap' library)
import argparse

parser = argparse.ArgumentParser(description='Scan a host for open ports, services, and banner grabbing')
parser.add_argument('-H', '--host', help='The target host IP address or URL', required=True)
args = parser.parse_args()

# Configuration
target = args.host.strip()
start_port = 1
end_port = 1024
MAX_THREADS = 100

# Thread-safe queue for ports
port_queue = Queue()
open_ports = []

def grab_banner(sock):
    try:
        sock.settimeout(1)
        return sock.recv(1024).decode('utf-8').strip()
    except Exception:
        return None

def scan_port(port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((target, port))
        if result == 0:
            banner = grab_banner(sock)
            report = f"Port {port} is open"
            if banner:
                report += f" | Banner: {banner}"
            open_ports.append((port, banner))
            print(report)
        sock.close()
    except Exception:
        pass

def worker():
    while not port_queue.empty():
        port = port_queue.get()
        scan_port(port)
        port_queue.task_done()

# Fill the port queue
for port in range(start_port, end_port + 1):
    port_queue.put(port)

# Start threads
threads = []
for _ in range(min(MAX_THREADS, end_port - start_port + 1)):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

port_queue.join()
for t in threads:
    t.join()

if nmap and open_ports:
    print("\n[+] Starting Port Scanning Service Detection...\n")
    nm = nmap.PortScanner()
    for port, _ in open_ports:
        res = nm.scan(target, str(port), arguments='-sV')
        try:
            service = res['scan'][target]['tcp'][port]['name']
            version = res['scan'][target]['tcp'][port].get('version', '')
            print(f"Port {port}: Service={service}, Version={version}")
        except KeyError:
            print(f"Port {port}: No service details found.")

else:
    if not nmap:
        print("\n[!] Nmap module not installed. Skipping service/version detection.")

