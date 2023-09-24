import socket
import threading

nickname = input('Enter nickname > ')
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = '127.0.0.1'
port = 8888
ADDR = (host,port)

client.connect(ADDR)

## Listening to server and sending nickname
def receive():
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if message == 'DHRUV':
                client.send(nickname.encode('ascii'))
            else:
                print(message)
        except:
            print('Error!!')
            client.close()
            break

def write():
    while True:
        message = '{}: {}'.format(nickname, input(''))
        client.send(message.encode('ascii'))

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()