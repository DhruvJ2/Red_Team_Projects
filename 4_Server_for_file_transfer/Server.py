import socket

IPADDR = 'localhost'
Port = 8888
ADDR = (IPADDR, Port)
FORMAT = 'utf-8'
bufferSize = 1024

ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ServerSocket.bind(ADDR)

ServerSocket.listen()
print("[Waiting For Connection].....")
connected = True

while True:
    conn, addr = ServerSocket.accept()              # Establishing Connection
    print(f'Connected to {addr}')
    data = conn.recv(bufferSize)

    file = open('File', 'rb')
    lines = file.readlines()
    while lines:
        conn.send(bytes(f'{lines}', FORMAT))
        print("File Sent")
        lines = file.read(bufferSize)
    file.close()
    conn.send(bytes("Thank you for connecting", FORMAT))
    conn.close()





