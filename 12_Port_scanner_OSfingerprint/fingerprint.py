import argparse
import nmap
import os
import socket

# Add Nmap executable path if not in system PATH (update this path if needed)
os.environ['PATH'] += r";C:\Program Files (x86)\Nmap"

def scanport(ip, ports):
    nm = nmap.PortScanner()
    nm.scan(ip, ports, arguments='-O -sV')

    if ip not in nm.all_hosts():
        print(f"No scan results for {ip}. It may be down, firewall blocked, or ports closed.")
        return []

    host_infos = []

    os_family = "Unknown"
    os_classes = nm[ip].get('osclass', [])
    if os_classes:
        os_family = os_classes[0].get('osfamily', 'Unknown')

    for proto in nm[ip].all_protocols():
        lport = nm[ip][proto].keys()
        for port in lport:
            host_info = {
                'ip': ip,
                'os': os_family,
                'port': port,
                'name': nm[ip][proto][port]['name'],
                'version': nm[ip][proto][port]['version'],
            }
            host_infos.append(host_info)
    return host_infos

def main():
    parser = argparse.ArgumentParser(description='Scan a host for open ports, services, and OS detection')
    parser.add_argument('-H', '--host', help='The target host IP address or URL', required=True)
    parser.add_argument('-p', '--ports', help='Ports to Scan', type=str, required=True)
    args = parser.parse_args()

    host_input = args.host.strip()

    # Remove http:// or https:// if present
    if host_input.startswith('http://') or host_input.startswith('https://'):
        host_input = host_input.split('://')[1]

    # Resolve domain to IP
    try:
        ip = socket.gethostbyname(host_input)
    except socket.gaierror:
        print(f"Could not resolve hostname: {host_input}")
        return

    port = args.ports

    print(f"\n{'='*60}")
    print(f" Starting scan for Host: {host_input} (IP: {ip})")
    print(f" Ports: {port}")
    print(f"{'='*60}\n")

    host_infos = scanport(ip, port)

    if not host_infos:
        print("No hosts found or no open ports detected.")
        return

    print(f"{'='*60}")
    print(f"{'Scan Results':^60}")
    print(f"{'='*60}")

    current_ip = None
    current_os = None
    for host_info in host_infos:
        if host_info['ip'] != current_ip or host_info['os'] != current_os:
            current_ip = host_info['ip']
            current_os = host_info['os']
            print(f"\nHost: {current_ip}")
            print(f"Detected OS: {current_os}")
            print(f"{'-'*60}")

        print(f" Port {host_info['port']:>5} | Service: {host_info['name']:<15} | Version: {host_info['version']}")

    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()
