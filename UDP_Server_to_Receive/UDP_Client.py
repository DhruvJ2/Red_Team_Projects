import socket
localIP = "localhost"
PORT = 8888
bufferSize = 1024
ADDR = (localIP, PORT)

# Create a scoket
UDPClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    msgFromClient = input("> ")
    bytesToSend = str.encode(msgFromClient)

    UDPClientSocket.sendto(bytesToSend, ADDR)

    message , addr = UDPClientSocket.recvfrom(bufferSize)
    msg = "\nMessage from Server: {} \n".format(message.decode('utf-8'))

    print(msg)