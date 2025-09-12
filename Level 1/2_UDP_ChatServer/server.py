import socket
import threading
import queue

host='127.0.0.1'
port=8888
ADDR = (host, port)

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(ADDR)

clients=[]
messages=queue.Queue()

def recieve():
    while True:
        try:
            message, addr=server.recvfrom(1024)
            messages.put((message, addr))
        except:
            pass

def broadcast():
    while True:
        while not messages.empty():
            message, addr = messages.get()
            print(message.decode())
            if addr not in clients:
                clients.append(addr)
            for client in clients:
                try:
                    if message.decode().startswith("SIGNUP_TAG:"):
                        name = message.decode()[message.decode().index(':')+1:]
                        server.sendto(f'{name} joined!'.encode() ,client)
                    else:
                        server.sendto(message, client)
                except:
                    clients.remove(client)

t1 = threading.Thread(target=recieve)    
t2 = threading.Thread(target=broadcast)

t1.start()
t2.start()
