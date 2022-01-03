import socket

IPADDR = 'localhost'
Port = 8888
ADDR = (IPADDR, Port)
FORMAT = 'utf-8'
bufferSize = 1024

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

clientSocket.connect(ADDR)
clientSocket.send(bytes('Hello Server!!!',FORMAT))

with open('received_file', 'wb') as file:
    print('File Opened')
    while True:
        print('Receiving data...')
        data = clientSocket.recv(bufferSize).decode()
        print(f'Data = {data}')
        if not data:
            break
        file.write(data.encode())
file.close()
print("successfully got the file")
clientSocket.close()
print("Server closed")