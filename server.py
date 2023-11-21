import time
import pickle
from threading import Thread
import socket
from utils import Utils


class Server(Utils):

    def __init__(self, clients=[], matrix=None):
        super().__init__()
        self.clients = clients
        size = 60
        self.matrix = [[None] * size for _ in range(size)]

    def run(self):
        try:
            print("BIND ADDRESS")
            self.sock.bind(self.address)

            print("LISTENING")
            self.sock.listen(100)
            print(self.address)

            while True:
                conn, addr = self.sock.accept()
                client = ClientHandler(conn, addr, self.BUFFER_SIZE, self)
                client.start()

                self.clients.append(client)
                print("NEW CLIENT", client, "\n")
                self.send_matrix(conn)
                self.list_all_clients()

        except Exception as e:
            print("line 35: ", e)
            self.sock.close()
            return

    def list_all_clients(self):
        print("ALL CLIENTS")
        for client in self.clients:
            print(client)

    def remove_client(self, clients, client):
        clients.remove(client)

    '''
    def broadcast(self, message, sender):
        timestamp = time.strftime("%H:%M:%S")
        for cl in self.clients:
            # if cl != sender:
            message_with_timestamp = f"\n[{timestamp}] ({sender}) : {message}"
            cl.sock.send(message_with_timestamp.encode("UTF-8"))
            print(f"SERVER: message '{message}' sent to {cl}")
    '''

    def send_matrix(self, conn):
        if len(self.clients) > 0:
            mattrix = ["matrix", self.matrix]
            data = pickle.dumps(mattrix)
            conn.send(data)
            # print(self.matrix)

    def update_matrix(self, x, y, color):
        if len(self.clients) > 0:
            for client in self.clients:
                colorButton = ["button", x, y, color]
                data = pickle.dumps(colorButton)
                client.sock.send(data)
            # print(self.matrix)


class ClientHandler(Thread, Utils):

    def __init__(self, sock, addr, BUFFER_SIZE, server):
        super().__init__()
        self.sock: socket.socket = sock
        self.addr = addr
        self.BUFFER_SIZE = BUFFER_SIZE
        self.server = server

    def run(self) -> None:

        while True:
            try:
                res = self.sock.recv(self.BUFFER_SIZE)
                data = pickle.loads(res)
                x, y, color = data[1], data[2], data[0]

                self.server.matrix[x][y] = color
                self.server.update_matrix(x, y, color)

            except (ConnectionResetError, ConnectionAbortedError, EOFError):
                print(f"DISCONNECT: client {self.addr} has disconnected")
                self.sock.close()
                self.server.remove_client(self.server.clients, self)
                self.server.list_all_clients()
                break

    def __repr__(self) -> str:
        return f"Client: {self.addr} with buffer size {self.BUFFER_SIZE}"

    def set_client_name(self, new_name):
        # with self.lock:
        old_name = self.addr
        self.addr = new_name
        print(f"Клиент {old_name} сменил имя на {new_name}.\n")


server = Server()
server.run()
