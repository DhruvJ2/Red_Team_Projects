import socket
import threading

host='127.0.0.1'
port=8888
ADDR=(host, port)

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.connect(ADDR)

name = input('nickname: ')

def receive():
    while True:
        try:
            message, _=client.recvfrom(1024)
            print(message.decode())
        except:
            pass

t1 = threading.Thread(target=receive)

t1.start()

client.sendto(f'SIGNUP_TAG:{name}'.encode(), ADDR)

while True:
    try:
        message= input('')
        if message=='q':
            exit()
        else:
            client.sendto(f'{name}: {message}'.encode(), ADDR)
    except:
        pass