import socket
import threading

nickname = input('Enter nickname > ')
shift = int(input('Enter a number between 1-25 >'))
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = '127.0.0.1'
port = 8888
ADDR = (host,port)

client.connect(ADDR)

#Encoding with Ceaser Cipher
def encrypt(text, shift):
    result = ""
    for char in text:
        if char.isupper():
            result += chr((ord(char) - 65 + shift) % 26 + 65)
        elif char.islower():
            result += chr((ord(char) - 97 + shift) % 26 + 97)
        else:
            result += char
    return result

#Decoding Ceaser Cipher
def decrypt(text, shift):
    result = ""
    for char in text:
        if char.isupper():
            result += chr((ord(char) - 65 - shift) % 26 + 65)
        elif char.islower():
            result += chr((ord(char) - 97 - shift) % 26 + 97)
        else:
            result += char
    return result

## Listening to server and sending nickname
def receive():
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if message == 'DHRUV':
                client.send(nickname.encode('ascii'))
            else:
                #Message format: nickname|shift: encrypted_text
                if "|":
                    try:
                        sender_shift_part, encrypted_text = message.split(": ", 1)
                        sender, sender_shift_str = sender_shift_part.split("|")
                        sender_shift = int(sender_shift_str)
                        decrypted_text = decrypt(encrypted_text, sender_shift)
                        print(f"{sender}: {decrypted_text}")
                    except ValueError:
                        # fallback if not properly formatted
                        print(message)
                else:
                    print(message)
        except:
            print('Error!!')
            client.close()
            break


## Listening to server and sending nickname
# def receive():
#     while True:
#         try:
#             message = client.recv(1024).decode('ascii')
#             if message == 'DHRUV':
#                 client.send(nickname.encode('ascii'))
#             else:
#                 # message format: "nickname: encrypted_text"
#                 if ": " in message:
#                     sender, encrypted_text = message.split(": ", 1)
#                     decrypted_text = decrypt(encrypted_text, shift)
#                     print(f"{sender}: {decrypted_text}")
#                 else:
#                     # fallback if format unexpected
#                     print(message)
#         except:
#             print('Error!!')
#             client.close()
#             break

def write():
    while True:
        text = input('')
        if text=='q':
            exit()
        else:
            encrypted_text = encrypt(text, shift)
            # send message with shift appended after nickname separated by |
            message = '{}|{}: {}'.format(nickname, shift, encrypted_text)
            client.send(message.encode('ascii'))


# def write():
#     while True:
#         text = input('')
#         text = encrypt(text, shift)
#         message = '{}: {}'.format(nickname, text)
#         client.send(message.encode('ascii'))

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
