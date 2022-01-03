import socket

server = socket.socket()
print("[Socket Created]")
ADDR = ('localhost', 8888)

server.bind(ADDR)

server.listen()
print("[Waiting for Connection..]")
connected=True

while True:
    conn, addr = server.accept()
    print(f"Connected to .. [{addr}]")

    conn.send(bytes("Welcome to chat server", 'utf-8'))
    conn.send(bytes("This server will only receive messages", 'utf-8'))

    while connected:
        msg = conn.recv(1024).decode()
        print(msg)
        if msg == "!Disconnect":
            print("[Connection Closed]")
            connected = False
    conn.close()


