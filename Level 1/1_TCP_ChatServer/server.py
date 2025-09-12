import socket
import threading

host='127.0.0.1'
port=8888

ADDR=(host,port)

server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind(ADDR)
server.listen()

clients=[]
nicknames=[]

## Send messages to all connected clients
def broadcast(message):
    for client in clients:
        client.send(message)

def handle(client):
    while True:
        # Broadcasting messages
        try:
            message = client.recv(1024)
            broadcast(message)
        except:
            ##Removing and closing clients
            index=client.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast('{} left!'.format(nickname).encode('ascii'))
            nicknames.remove(nickname)
            break

# Recieving and listening functions
def recieve():
    while True:
        #accept connection
        client, addr = server.accept()
        print(f'Connected with {addr}')

        # request and store nicknames
        client.send('DHRUV'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        nicknames.append(nickname)
        clients.append(client)

        print("Nickname is {}".format(nickname))
        broadcast('{} joined!'.format(nickname).encode('ascii'))
        client.send('Connected to the server!'.encode('ascii'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

recieve()