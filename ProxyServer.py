import threading
import socket
import ssl

class Server:
    HOST = '127.0.0.1'
    PORT = 8080
    blocklist = ['www.reddit.com']
    status = True
    
    def __init__(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((self.HOST, self.PORT))
        self.serverSocket.listen(10)
        self.clients = {}
        self.no_clients = 0
        self.status=True

    def server_listen(self):
        print("Server waiting for connections..."   )
        while self.status:
            (conn, addr) = self.serverSocket.accept()
            t = threading.Thread(name=self.getClientName(addr), target=self.server_thread  , args=(conn, addr))
            t.setDaemon(True)
            t.start()
        self.serverSocket.close()


    def server_thread(self, conn, addr):
        req = conn.recv(1024)
        if len(req) < 3:
            conn.close()
            return
        parseReq = str(req).split('\n')
        first_line = parseReq[0].split(' ')
        url = first_line[1]
        request_type = first_line[0][2:]

        addressStart = url.find('://')
        if addressStart == -1:
            url = url.split(':')
            address = url[0]
            port = int(url[1])
        else:
            address = url[addressStart+3:len(url)-1]
            port = 80

        print("Incoming", request_type, "request from", addr, "to", address)
        if address in self.blocklist:
            conn.send(b'HTTP/1.1 403 Forbidden')
            print("Can't access blacklisted address: ", address)
            conn.close()
            return
    

        if request_type == 'CONNECT':
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as  s:
                s.connect((address, port))
                res = "HTTP/1.0 200 Connection established\r\nProxy-agent: Mike\r\n\r\n"
                conn.sendall(res.encode())
                conn.setblocking(0)
                s.setblocking(0)  

                while True:
                    try:
                        data = conn.recv(1024)
                        s.sendall(data)
                    except socket.error as msg:
                        pass
                    try:
                        data = s.recv(1024)
                        conn.sendall(data)
                    except socket.error as msg:
                        pass
        else:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as  s:
                    s.connect((address, port))
                    s.sendall(req)

                    while True:
                        data = s.recv(1024)
                        if len(data) > 0:
                            conn.sendall(data)
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
    t = threading.Thread(name='listener', target=server.server_listen, args=())
    t.setDaemon(True)
    print("Web Proxy Server Management Console")
    print("Type \'help\' for list of commands\n")
    while server.status:
        command = input()
        if command=='help':
            print("\nhelp\t\tDisplay commands\n" +
            "start\t\tBeginning listening for connections\n" +
            "exit\t\tExit the program\n" +
            "block (url)\tBlock connections from and to specified url\n" +
            "blocklist\tShow currently blocked urls\n")
        elif command=='start':
            t.start()
        elif command=='exit':
            server.status = False
        elif command=='blocklist':
            print(server.blocklist)
        elif command[0:5]=='block':
            server.blocklist.append(command[6:])
        elif command[0:7]=='unblock':
            server.blocklist.remove(command[8:])
        else:
            print("Unkown command:",command)
    main_t = threading.currentThread()
    for t in threading.enumerate():
        if t is not main_t:
            t.join()
    print("Program exiting...")

        