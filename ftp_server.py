from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

def main():
    #User authorization
    authorizer = DummyAuthorizer()
    #Add User 
    authorizer.add_user("user","12345","D:/", perm="elradfmw")
    #Anonymous user
    authorizer.add_anonymous("D:/")

    #Ftp handler
    handler = FTPHandler
    handler.authorizer = authorizer

    # Server settings (IP and Port)
    server = FTPServer(("0.0.0.0", 21), handler=handler)

    # maximum Connections
    server.max_cons = 256
    server.max_cons_per_ip = 5

    print("FTP Server started. IP: 0.0.0.0, Port: 21")
    #Start Server
    server.serve_forever()

if __name__ == "__main__":
    main()