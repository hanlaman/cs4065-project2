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

class ProtocolQueries:
    def groups() -> str:
        return "GROUPS"
    def users(group: str) -> str:
        return f"USERS|{group}"
    def join(group: str, name: str) -> str:
        return f"JOIN|{group}|{name}"
    def leave(group: str) -> str:
        return f"LEAVE|{group}"
    def post(group: str, subject: str, content: str) -> str:
        return f"POST|{group}|{subject}|{content}"
    def view(id: UUID) -> str:
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
    def getUserName(self) -> str: return self._userNameVar.get()
    def _handleConnect(self):
        if self._hostVar.get() == "" or self._portVar.get() == "": return
        self._server.connect(self._hostVar.get(), int(self._portVar.get()))
        if (self._server.connected): self._onConnected()

class MainFrame(Frame):
    def __init__(self, parent, server: Server) -> None:
        Frame.__init__(self, parent)
        self._server = server
        self._server.send(ProtocolQueries.join('Public', userName)) # JOIN public
        self._joinFrame = JoinFrame(self, server, ['Group1', 'Group2', 'Group3', 'Group4', 'Group5']) # PRESET, need to query
        self._joinFrame.grid(row=0, column=0)
        self._sep = ttk.Separator(self, orient='horizontal')
        self._sep.grid(row=1, column=0)
        self._chats = ChatsFrame(self)
        self._chats.grid(row=2, column=0)
        self._msgFrame = MessagingFrame(self)
        self._msgFrame.grid(row=3, column=0)

class JoinFrame(Frame):
    def __init__(self, parent, server: Server, groups: list[str]) -> None:
        Frame.__init__(self, parent)
        self._server = server
        self._groupVar = StringVar()
        self._groups = ttk.Combobox(self, values=groups, state="readonly", textvariable=self._groupVar)
        self._groups.grid(row=0, column=0)
        self._joinButton = Button(self, text="Join", command=self._handleJoin)
        self._joinButton.grid(row=0, column=1)
    def _handleJoin(self) -> None:
        self._server.send(ProtocolQueries.join(self._groupVar.get(), userName))

class ChatsFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self._nb = ttk.Notebook(self)
        self._nb.grid(row=0, column=0)
        self._publicChat = ChatFrame(self)
        self._nb.add(self._publicChat, text='public')

class ChatFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self._users = UsersFrame(self)
        self._users.grid(row=0, column=0)
        self._messages = MessagesFrame(self)
        self._messages.grid(row=0, column=1)
        self._details = DetailFrame(self)
        self._details.grid(row=0, column=2)

class UsersFrame(LabelFrame):
    def __init__(self, parent):
        LabelFrame.__init__(self, parent, text="Users")
        self._users = Listbox(self)
        self._users.grid(row=0, column=0)

class MessagesFrame(LabelFrame):
    def __init__(self, parent):
        LabelFrame.__init__(self, parent, text="Messages")
        self._messages = Listbox(self)
        self._messages.grid(row=0, column=0)


class DetailFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self._senderVar = StringVar()
        self._senderLabel = Label(self, text="From: ")
        self._senderLabel.grid(row=0, column=0)
        self._senderEntry = Entry(self, textvariable=self._senderVar)
        self._senderEntry.grid(row=0, column=1)
        self._dateVar = StringVar()
        self._dateLabel = Label(self, text="Date: ")
        self._dateLabel.grid(row=1, column=0)
        self._dateEntry = Entry(self, textvariable=self._dateVar)
        self._dateEntry.grid(row=1, column=1)
        self._subjectVar = StringVar()
        self._subjectLabel = Label(self, text="Subject: ")
        self._subjectLabel.grid(row=2, column=0)
        self._subjectEntry = Entry(self, textvariable=self._subjectVar)
        self._subjectEntry.grid(row=2, column=1)
        self._content = Text(self, width=20, height=5)
        self._content.grid(row=3, column=0, columnspan=2)
        self._leaveButton = Button(self, text="Leave", command=self._onLeave)
        self._leaveButton.grid(row=4, column=0, columnspan=2)
    def _onLeave(self):
        pass

class MessagingFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self._subjectVar = StringVar()
        self._subjectLabel = Label(self, text="Subject")
        self._subjectEntry = Entry(self, textvariable=self._subjectVar)
        self._subjectLabel.grid(row=0, column=0)
        self._subjectEntry.grid(row=0, column=1)
        self._contentVar = StringVar()
        self._contentLabel = Label(self, text="Content")
        self._contentEntry = Entry(self, textvariable=self._contentVar)
        self._contentLabel.grid(row=0, column=2)
        self._contentEntry.grid(row=0, column=3)
        self._postButton = Button(self, text="Post", command=self._onPost)
        self._postButton.grid(row=0, column=4)
    def _onPost(self):
        pass

def onResponseReceived(response: str):
    """This will handle messages received from the server"""
    print(response)

def onConnected():
    # start listening for server messages
    server.listen(onResponseReceived)
    # Swap connection frame with main
    conn.destroy()
    main = MainFrame(root, server)
    main.grid(row=0, column=0)

root = Tk()
root.title("Client")

userName: str | None = None
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