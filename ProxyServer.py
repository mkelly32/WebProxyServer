import threading
import socket
import signal


class Server:
    HOST = 'localhost'
    PORT = 8080
    
    def __init__(self):
        signal.signal(signal.SIGINT, self.shutdown) 
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((self.HOST, self.PORT))
        self.serverSocket.listen(10)
        self.clients = {}

    def server_listen(self):
        print("Server waiting for connections..."   )
        while True:
            (conn, addr) = self.serverSocket.accept()
            d = threading.Thread(name=self._getClientName(addr))
            target = self.proxy_thread, args=(conn, addr)
            d.setDaemon(True)
            d.start()
