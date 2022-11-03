import socket

localIP = "localhost"
PORT = 8888
bufferSize = 1024
ADDR = (localIP, PORT)

bytesToSend = str.encode("Hello UDP Client")

# Create a scoket
UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket
UDPServerSocket.bind(ADDR)

print("UDP Server is up and Running")

while True:
    message, addr = UDPServerSocket.recvfrom(bufferSize)

    clientmessage = "Message From Client: {}".format(message.decode('utf-8'))
    clientIP = "Client IP Address: {}".format(addr)

    print(clientmessage+"\n"+clientIP)

    UDPServerSocket.sendto(bytesToSend, addr)

