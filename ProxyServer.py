import threading
import socket
import sys
import utils
import urllib

class Server:
    HOST = '127.0.0.1'
    PORT = 8080
    blocklist = []
    status = True
    
    def __init__(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((self.HOST, self.PORT))
        self.serverSocket.listen(10)
        self.clients = {}
        self.no_clients = 0

    def server_listen(self):
        print("Server waiting for connections..."   )
        local = threading.local()
        while self.status:
            (conn, addr) = self.serverSocket.accept()
            (ip, port) = addr
            if (self.HOST==ip):
                t = threading.Thread(name=self.getClientName(addr), target=self.server_thread  , args=(conn, addr))
            else:
                t = threading.Thread(name=self.getClientName(addr), target=self.client_thread, args=(conn, addr, local))
            t.setDaemon(True)
            t.start()
        self.serverSocket.close()

    def client_thread(self, conn, addr, local):
        try:
            print("Connecion from: ", addr)
            conn.settimeout(1)
            local.data = conn.recv(1024)
            if local.data=="":
                return
            parsedReq = self.parseReq(addr, local.data)
            self.respond(parsedReq, conn)
        finally:
            conn.close()

    def respond(self, data, conn):
        res = ""
        if 'ERROR' in data:
            res = self.createResponse()
            conn.sendall(res)

    def parseReq(self, addr, data):
        req = utils.HTTPRequest(data)        
        req.path = url = urllib.unquote(req.path).decode('utf-8')

        if req.error_code is not None:
            return {
                        'ERROR': {
                            'msg': req.error_message,
                            'error_code': req.error_code
                        }
                }
        if req.headers['host'] in self.blocklist:
            return {
                        'ERROR': {
                            'msg' : "Host is in blocklist",
                            'error_code': 403
                        }
                }
        else:
            return {}


    def server_thread(self, conn, addr):
        req = conn.recv(1024)
        if len(req) < 3:
            conn.close()
            return
        first_line = str(req).split('\n')[0]
        url = first_line.split(' ')[1]
        print(url)
        if url in self.blocklist:
            print("Can't access blacklisted url: ", url)
            conn.close()
            return

        print("Incoming ", first_line.split(' ')[0][2:], "request from browser")

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

def exitProgram(server):
    print("Exiting program...")
    
    print("Done")
    quit()

if __name__ == '__main__':
    server = Server()
    t = threading.Thread(name='listener', target=server.server_listen, args=())
    t.setDaemon(True)
    print("Web Proxy Server Management Console")
    print("Type \'help\' for list of commands\n")
    status = True
    while status:
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
            status = False
        elif command.find('block, beg=0'):
            server.blocklist.append(command[4:])
        elif command=='blocklist':
            print(server.blocklist)
        else:
            print("Unkown command: ",command +"\n")
    main_t = threading.currentThread()
    for t in threading.enumerate():
        if t is main_t:
            continue
        t.join()
    print("Program exiting...")

        