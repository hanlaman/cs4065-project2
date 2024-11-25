
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread
from typing import Callable

class Server:
    def __init__(self) -> None:
        self._socket: socket | None = None
        self.connected = False
    def connect(self, host: str, port: int):
        self._socket = socket(AF_INET, SOCK_STREAM)
        self.connected = self._socket.connect_ex((host, port)) == 0
    def disconnect(self):
        self.connected = False
        if self._socket:
            self._socket.close()
            self._socket = None
    def send(self, msg: str) -> None:
        if not self._socket:
            raise RuntimeError("Socket not connected")
        fmsg = f"{msg}\n"
        self._socket.sendall(fmsg.encode('utf-8'))
    def listen(self, handle: Callable[[str], None]) -> Thread:
        if not self._socket:
            raise RuntimeError("Socket not connected")
        def listen_thread():
            buffer = ""
            while self.connected:
                data: str
                try:
                    data = self._socket.recv(1024).decode('utf-8')
                except Exception as e:
                    self.connected = False
                    self._socket = None
                    break
                if not data:
                    break # Socket closed by server
                buffer += data
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    handle(message)
        listener = Thread(target=listen_thread, daemon=True)
        listener.start()
        return listener

def onMsgReceived(msg: str):
    print("! " + msg)

server = Server()
host = input("Host: ")
port = int(input("Port: "))
server.connect(host, port)
if not server.connected:
    exit(1)
print("Connected!")
listener = server.listen(onMsgReceived)
print("Listening for server messages...")
while (True):
    cmd = input()
    if cmd == "close":
        server.disconnect()
        break
    try:
        server.send(cmd)
    except RuntimeError:
        break
listener.join()
print("Disconnected")