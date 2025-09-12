import socket
import threading

host='127.0.0.1'
port=8888
ADDR=(host, port)

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.connect(ADDR)

name = input('nickname> ')
rot13 = str.maketrans(
    'ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz',
    'NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm'
)

#Since ROT13 cipher is symmetric encryption and decryption is same
def transform(text):
    return text.translate(rot13)

def receive():
    while True:
        try:
            encrypted_message, _=client.recvfrom(1024)
            message = transform(encrypted_message.decode())
            print(message)
        except:
            print('Error!')

client.sendto(f'SIGNUP_TAG: {transform(name)}'.encode(), ADDR)

def write():
    while True:
        try:
            message= input('')
            message = transform(message)
            if message=='q':
                client.sendto(f'{name} has left!'.encode(), ADDR)
                exit()
                break
            else:
                client.sendto(f'{name}: {message}'.encode(), ADDR)
        except:
            print('Error!')
            exit()
            break

t1 = threading.Thread(target=receive)
t1.start()
t2 = threading.Thread(target=write)
t2.start()