from socket import socket, AF_INET, SOCK_STREAM
from time import sleep
from tkinter import *
from tkinter import ttk
from typing import Callable
from threading import Thread
from datetime import datetime
from uuid import UUID

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
    def listen(self, handle: Callable[[str], None]) -> None:
        if not self._socket:
            raise RuntimeError("Socket not connected")
        def listen_thread():
            buffer = ""
            try:
                while self.connected:
                    data = self._socket.recv(1024).decode('utf-8')
                    if not data:
                        break # Socket closed by server
                    buffer += data
                    while '\n' in buffer:
                        message, buffer = buffer.split('\n', 1)
                        handle(message)
            except Exception as e:
                raise e
            finally:
                self.connected = False
                self._socket.close()
        Thread(target=listen_thread, daemon=True).start()

class ProtocolQueries:
    def groups():
        return "GROUPS"
    def users(group: str):
        return f"USERS|{group}"
    def join(group: str, name: str):
        return f"JOIN|{group}|{name}"
    def leave(group: str):
        return f"LEAVE|{group}"
    def post(group: str, subject: str, content: str):
        return f"POST|{group}|{subject}|{content}"
    def view(id: UUID):
        return f"VIEW|{id}"
    
class ProtocolResponses:
    def parseGroups(msg: str):
        # GROUPS|g1|g2|g3
        return msg.split("|")[1:]
    def parseUsers(msg: str) -> tuple[str, list[str]]:
        # USERS|group|usr1|usr2|...
        parts = msg.split("|")
        return [parts[1], parts[2:]]
    def parseJoin(msg: str) -> tuple[str, str]:
        # JOIN|group|name
        parts = msg.split("|")
        return [parts[1], parts[2]]
    def parseLeave(msg: str) -> tuple[str, str]:
        # LEAVE|group|name
        parts = msg.split("|")
        return [parts[1], parts[2]]
    def parseMessage(msg: str) -> tuple[str, str]:
        # MESSAGE|group|id
        parts = msg.split("|")
        return [parts[1], parts[2]]
    def parseView(msg: str) -> tuple[UUID, str, datetime, str, str]:
        # VIEW|id|sender|postDate|subject|contents
        parts = msg.split("|")
        return [UUID(parts[1]), parts[2], datetime.fromisoformat(parts[3]), parts[4], parts[5]]
    
class ConnectionFrame(Frame):
    def __init__(self, parent, server: Server, onConnected: Callable[[], None]) -> None:
        Frame.__init__(self, parent)
        self._server = server
        self._onConnected = onConnected
        self._userNameVar = StringVar()
        self._userNameLabel = Label(self, text="User Name")
        self._userNameEntry = Entry(self, textvariable=self._userNameVar)
        self._userNameLabel.grid(row=0, column=0)
        self._userNameEntry.grid(row=0, column=1)
        self._hostVar = StringVar()
        self._hostLabel = Label(self, text="Host")
        self._hostEntry = Entry(self, textvariable=self._hostVar)
        self._hostLabel.grid(row=1, column=0)
        self._hostEntry.grid(row=1, column=1)
        self._portVar = StringVar()
        self._portLabel = Label(self, text="Port")
        self._portEntry = Entry(self, textvariable=self._portVar)
        self._portLabel.grid(row=2, column=0)
        self._portEntry.grid(row=2, column=1)
        self._connectButton = Button(self, text="Connect", command=self._handleConnect)
        self._connectButton.grid(row=3, column=0, columnspan=2)
    def _handleConnect(self):
        if self._hostVar.get() == "" or self._portVar.get() == "": return
        self._server.connect(self._hostVar.get(), int(self._portVar.get()))
        if (self._server.connected): self._onConnected()

class MainFrame(Frame):
    def __init__(self, parent, server: Server) -> None:
        Frame.__init__(self, parent)
        self._server = server
        # TODO
        self._tempLabel = Label(self, text="Main Frame")
        self._tempLabel.grid(row=0, column=0)

def onResponseReceived(response: str):
    """This will handle messages received from the server"""
    print(response)

def onConnected():
    server.listen(onResponseReceived)
    # Swap connection frame with main
    conn.destroy()
    main = MainFrame(root, server)
    main.grid(row=0, column=0)

root = Tk()
root.title("Client")
server = Server()

conn = ConnectionFrame(root, server, onConnected)
conn.grid(row=0, column=0)

# Close resources on window exit
def onClosing():
    if server.connected:
        server.disconnect()
    root.destroy()
root.protocol("WM_DELETE_WINDOW", onClosing)

root.mainloop()