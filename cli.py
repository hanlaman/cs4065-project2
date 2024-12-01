
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread
from typing import Callable

# managing client-server connection 
class Server:
    def __init__(self) -> None:
        self._socket: socket | None = None # placeholder for socket connection
        self.connected = False # tracks connection status with server

    # connects to server at specified host and port 
    def connect(self, host: str, port: int):
        self._socket = socket(AF_INET, SOCK_STREAM) # creates a socket for tcp communication
        # attempt to connect to server and update connection status 
        self.connected = self._socket.connect_ex((host, port)) == 0
    # disconnect from server and clean up
    def disconnect(self):
        self.connected = False # update connection status 
        if self._socket:
            self._socket.close() # close socket 
            self._socket = None # reset socket to none

    # send a message to the server
    def send(self, msg: str) -> None:
        if not self._socket:
            raise RuntimeError("Socket not connected") # raise error if not connected 
        fmsg = f"{msg}\n"
        self._socket.sendall(fmsg.encode('utf-8')) # send encoded message to server 

    # listen for incoming messages from server 
    def listen(self, handle: Callable[[str], None]) -> Thread:
        if not self._socket:
            raise RuntimeError("Socket not connected")

        # define listening logic to run in a separate thread 
        def listen_thread():
            buffer = "" # buffer to store partial messages 
            while self.connected:
                data: str
                try:
                    # recieve data from server and decode it 
                    data = self._socket.recv(1024).decode('utf-8')
                except Exception as e:
                    # handle exceptions such as disconnect 
                    self.connected = False
                    self._socket = None
                    break
                if not data:
                    break # Socket closed by server
                buffer += data # append received data to the buffer 
                while '\n' in buffer:
                    # extract and process complete messages from buffer 
                    message, buffer = buffer.split('\n', 1)
                    handle(message) # pass message to handler function

        # start listening logic in new daemon thread 
        listener = Thread(target=listen_thread, daemon=True)
        listener.start()
        return listener
# callback function to handle messages received from the server 
def onMsgReceived(msg: str):
    print("! " + msg)

# start of main program 
server = Server()
host = input("Host: ")
port = int(input("Port: "))
# attempt to connect to server 
server.connect(host, port)
if not server.connected:
    exit(1)
print("Connected!") # confirm successful connection 
# start listening for messages from server 
listener = server.listen(onMsgReceived)
print("Listening for server messages...")
# main loop to send commands to server 
while (True):
    cmd = input()
    if cmd == "close":
        server.disconnect()
        break
    try:
        server.send(cmd)
    except RuntimeError:
        break
listener.join() # wait for lsitener thread to finish
print("Disconnected") # confirm disconnection
