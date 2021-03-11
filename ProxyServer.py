import threading
import socket
import signal


class Server:
    HOST = '127.0.0.1'
    PORT = 8080
    blacklist = []
    
    def __init__(self):
        #signal.signal(signal.SIGINT, self.shutdown) 
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((self.HOST, self.PORT))
        self.serverSocket.listen(10)
        self.clients = {}
        self.no_clients = 0

    def server_listen(self):
        print("Server waiting for connections..."   )
        while True:
            (conn, addr) = self.serverSocket.accept()
            d = threading.Thread(name=self.getClientName(addr), target=self.server_threads  , args=(conn, addr))
            target = self.proxy_thread, args=(conn, addr)
            d.setDaemon(True)
            d.start()

    def server_threads(self, conn, addr):
        req = conn.recv(1024)
        print(req)
        first_line = str(req).split('\n')[0]
        url = first_line.split(' ')[1]
        if url in self.blacklist:
            print("Can't access blacklisted url: ", url)
            conn.close()
            return

        print("Incoming ", url[0], "request from browser")

        #Parse  the request for destination port and address
        address_start = url.find("://")
        if address_start == -1:
            temp = url
        else:
            temp = url[(address_start+3):]

        port_position = temp.find(":")
        address_end = temp.find("/")
        if address_end == -1:
            address_end = len(temp)
        
        address = ""
        port = -1
        if port_position == -1 or address_end << port_position:
            port = 80
            address = temp[:address_end]
        else:
            port = int((temp[(port_position+1):])[:address_end-port_position-1])
            address = temp[:port_position]

        #Connect to the addresss in request
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as  s:
                s.settimeout(5)
                s.connect((address, port))
                s.sendall(req)

                while True:
                    data = s.recv(1024)
                    if len(data) > 0:
                        conn.send(data)
                    else:
                        break
                conn.close()
        
        except socket.error as msg:
            print("Erorr: ", msg)
            if conn:
                conn.close()
            print("Warning, reseting ", addr)

    def getClientName(self, addr):
        lock = threading.Lock()
        lock.acquire()
        client_address = addr[0]
        if client_address in self.clients:
            lock.release()
            return str(self.clients[client_address])
        
        self.clients[client_address] = self.no_clients
        self.no_clients += 1
        lock.release()
        return str(self.clients[client_address])

if __name__ == '__main__':
    server = Server()
    server.server_listen()


