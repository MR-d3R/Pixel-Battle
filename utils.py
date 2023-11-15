import socket
import threading


class Utils:

    def __init__(
            self,
            sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            address=("176.52.113.187", 8000),
            BUFFER_SIZE=4096,
            lock=threading.Lock(),
    ):
        self.sock = sock
        self.address = address
        self.BUFFER_SIZE = BUFFER_SIZE
        self.lock = lock

    def receive_data(self, connection: socket) -> bytearray:
        result = bytearray()
        while True:
            try:
                data = connection.recv(self.BUFFER_SIZE)
            except Exception as error:
                print(f"Ошибка {error}")
                return bytearray()
            else:
                if not data:
                    break
                result.extend(data)
                connection.send(b"OK")
        return result
