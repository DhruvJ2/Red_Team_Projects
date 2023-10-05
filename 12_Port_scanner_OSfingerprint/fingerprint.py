import argparse
import nmap

def scanport(ip, ports):
    nm = nmap.PortScanner()
    nm.scan(ip,ports)
    host_infos = []

    for proto in nm[ip].all_protocols():
        lport = nm[ip][proto].keys()
        for port in lport:
            host_info={
                'ip':ip,
                'os': nm[ip].get('osclass', {}).get('osfamily', 'Unknown'),
                'port': port,
                'name': nm[ip][proto][port]['name'],
                'version': nm[ip][proto][port]['version'],
            }   
            host_infos.append(host_info)
    return host_infos

def main():
    parser = argparse.ArgumentParser(description='Scan a host for open ports and services')
    parser.add_argument('host', help='The target host IP address')
    parser.add_argument('-p','--ports', help='Ports to Scan', type=str, required=True)
    args= parser.parse_args()

    ip = args.host
    port = args.ports

    print(f'Scanning IP: {ip}')
    print(f'Scanning ports: {port}')

    host_infos= scanport(ip, port)

    print(f'\n\nScan Results:')
    for host_info in host_infos:
        print(f"IP: {host_info['ip']}")
        print(f"Port: {host_info['port']}")
        print(f"Name: {host_info['name']}")
        print(f"OS: {host_info['os']}")
        print(f"Version: {host_info['version']}")

main()