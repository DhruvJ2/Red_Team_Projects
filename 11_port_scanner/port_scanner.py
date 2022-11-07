
from datetime import datetime
import pyfiglet
import socket
import time

asciiBanner = pyfiglet.figlet_format("Port Scanner")
print(asciiBanner)

soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

target = input('Enter IP to scan \n> ')

targetIp = socket.gethostbyname(target)

print('-' * 50)
print(f'Scanning target : {targetIp}')
print(f'Scanning started at : {str(datetime.now())}' )
print('-' * 50)

start = time.ctime()

def scan(port):
    try:
        soc.connect((targetIp,port))
        return True
    except:
        return False

for port in range(0,1000):
    if scan(port):
        print(f'Port {port} is Open')
    else:
        continue

soc.close()
end = time.ctime()
print(f'time taken : {start}-{end}')