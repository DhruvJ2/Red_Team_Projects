import socket

client = socket.socket()
ADDR = ('localhost', 8888)

client.connect(ADDR)
connected = True
print(client.recv(1024).decode())
print(client.recv(1024).decode())
while connected:
    msg = input("> ")
    client.sendall(bytes(msg, 'utf-8'))
    if msg == "!Disconnect":
        connected = False
    else:
        continue
