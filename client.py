from socket import socket, AF_INET, SOCK_STREAM
import sys
from tkinter import *
from tkinter import ttk
from typing import Callable

server: socket = socket(AF_INET, SOCK_STREAM)
userName: str | None = None

root = Tk()
root.title("Client")

class ConnectionFrame(Frame):
    def __init__(self, parent, socket: socket, onConnected: Callable[[], None]):
        Frame.__init__(self, parent)
        self._socket = socket
        self._onConnected = onConnected

        self._userNameVar = StringVar()
        self._userNameLabel = ttk.Label(self, text="User Name")
        self._userNameLabel.grid(column=0, row=0)
        self._userNameEntry = ttk.Entry(self, textvariable=self._userNameVar)
        self._userNameEntry.grid(column=1, row=0)

        self._addressVar = StringVar()
        self._addressLabel = ttk.Label(self, text="Address")
        self._addressLabel.grid(column=0, row=1)
        self._addressEntry = ttk.Entry(self, textvariable=self._addressVar)
        self._addressEntry.grid(column=1, row=1)

        self._portVar = StringVar()
        self._portLabel = ttk.Label(self, text="Port")
        self._portLabel.grid(column=0, row=2)
        self._portEntry = ttk.Entry(self, textvariable=self._portVar)
        self._portEntry.grid(column=1, row=2)

        self._connectButton = ttk.Button(self, text="Connect", command=self._connect)
        self._connectButton.grid(row=3, column=0, columnspan=2)

    def _connect(self):
        address = self._addressVar.get()
        portStr = self._portVar.get()
        if self._userNameVar.get() == "" or address == "" or portStr == "":
            return
        try:
            port = int(portStr)
            self._socket.connect((address, port))
        except Exception:
            error = ttk.Label(self, text="Could not connect")
            error.grid(column=0, row=4, columnspan=2)
            error['foreground'] = 'red'
            return
        
        self._onConnected()
    def getUserName(self):
        return self._userNameVar.get()

class JoinFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self._choicesVar = StringVar()

        self._choices = ttk.Combobox(self, textvariable=self._choicesVar, values=self._getGroups(), state="readonly")
        self._choices.grid(row=0, column=0)

        self._joinButton = ttk.Button(self, text="Join", command=self._onJoin)
        self._joinButton.grid(row=0, column=1)
    def _onJoin(self):
        choiceStr = self._choices.get()
        pass
    def _getGroups(self):
        return ('Group 1', 'Group 2', 'Group 3', 'Group 4', 'Group 5')
    
class ChatFrame(Frame):
    def __init__(self, parent, onLeave):
        Frame.__init__(self, parent)
        self._messages = Text(self, )
        self._subjectVar = StringVar()
        self._subjectEntry = ttk.Entry(self, textvariable=self._subjectEntry)
        self._contentVar = StringVar()
        self._contentEntry = ttk.Entry(self, textvariable=self._contentVar)
        self._postButton = ttk.Button(self, text="Post", command=self._onPost)
        self._leaveButton = ttk.Button(self, text="Leave", command=self._onLeave)

    def _onPost():
        pass
    def _onLeave():
        pass

class ChatsFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)

class MainFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self._joinFrame = JoinFrame(self)
        self._joinFrame.grid(row=0, column=0)
        self._separator = ttk.Separator(self, orient="horizontal")
        self._separator.grid(row=1, column=0)
        self._chatsFrame = ChatsFrame(self)
        self._chatsFrame.grid(row=2, column=0)

def onConnect():
    userName = connectionFrame.getUserName()
    # Swap connection frame to main app frame
    connectionFrame.destroy()
    mainFrame = MainFrame(root)
    mainFrame.grid(row=0, column=0)

# Start with connection frame
connectionFrame = ConnectionFrame(root, server, onConnect)
connectionFrame.grid(row=0, column=0)

# Close resources on window exit
def on_closing():
    if server is not None:
        server.close()
    root.destroy()
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()