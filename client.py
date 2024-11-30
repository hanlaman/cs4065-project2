from socket import socket, AF_INET, SOCK_STREAM
from tkinter import *
from tkinter import ttk
from typing import Callable
from threading import Thread
from datetime import datetime

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

def createGroupsQuery() -> str:
    return "GROUPS"
def createJoinQuery(group: str, name: str) -> str:
    return f"JOIN|{group}|{name}"
def createLeaveQuery(group: str) -> str:
    return f"LEAVE|{group}"
def createPostQuery(group: str, subject: str, content: str) -> str:
    return f"POST|{group}|{subject}|{content}"
def createViewQuery(group: str, id: int) -> str:
    return f"VIEW|{group}|{id}"
def createExitQuery():
    return 'EXIT'

def parseGroupsMsg(msg: str):
    # GROUPS|g1|g2|g3|...
    return msg.split("|")[1:]
def parseJoinMsg(msg: str) -> tuple[str, str]:
    # JOIN|group|name
    parts = msg.split("|")
    return [parts[1], parts[2]]
def parseLeaveMsg(msg: str) -> tuple[str, str]:
    # LEAVE|group|name
    parts = msg.split("|")
    return [parts[1], parts[2]]
def parseMessageMsg(msg: str) -> tuple[str, int]:
    # MESSAGE|group|id
    parts = msg.split("|")
    return [parts[1], int(parts[2])]
def parseViewMsg(msg: str) -> tuple[str, int, str, datetime, str, str]:
    # VIEW|group|id|sender|postDate|subject|contents
    parts = msg.split("|")
    return [parts[1], int(parts[2]), parts[3], datetime.fromisoformat(parts[4]), parts[5], parts[6]]
    
class ConnectionFrame(Frame):
    def __init__(self, parent, onConnected: Callable[[], None]) -> None:
        Frame.__init__(self, parent)
        self._onConnected = onConnected
        self._userNameVar = StringVar()
        self._userNameLabel = Label(self, text="User Name")
        self._userNameEntry = Entry(self, textvariable=self._userNameVar)
        self._hostVar = StringVar()
        self._hostLabel = Label(self, text="Host")
        self._hostEntry = Entry(self, textvariable=self._hostVar)
        self._portVar = StringVar()
        self._portLabel = Label(self, text="Port")
        self._portEntry = Entry(self, textvariable=self._portVar)
        self._connectButton = Button(self, text="Connect", command=self._handleConnect)
        self._placeFrames()
    def _placeFrames(self):
        self._userNameLabel.grid(row=0, column=0)
        self._userNameEntry.grid(row=0, column=1)
        self._hostLabel.grid(row=1, column=0)
        self._hostEntry.grid(row=1, column=1)
        self._portLabel.grid(row=2, column=0)
        self._portEntry.grid(row=2, column=1)
        self._connectButton.grid(row=3, column=0, columnspan=2)
    def _handleConnect(self):
        host = self._hostVar.get()
        portStr = self._portVar.get()
        if self._hostVar.get() == "" or self._portVar.get() == "":
            return
        server.connect(host, int(portStr))
        if (server.connected):
            self._onConnected()
    def getUserName(self) -> str: return self._userNameVar.get()

class MainFrame(Frame):
    def __init__(self, parent, userName: str) -> None:
        Frame.__init__(self, parent)
        self.userName = userName
        self._joinFrame = JoinFrame(self, [], userName) # Create join frame
        self._sep = ttk.Separator(self, orient='horizontal') # Create separator
        self._groups = GroupsFrame(self, self._handleLeaveClicked) # Create groups frame
        self._msgFrame = MessagingFrame(self, self._handlePostClicked) # Create msg frame
        self._placeFrames() # arrange the components of the main frame
        server.send(createGroupsQuery()) # Send a query for groups
    def _placeFrames(self):
        self._joinFrame.grid(row=0, column=0) # Place join frame
        self._sep.grid(row=1, column=0) # Place separator
        self._groups.grid(row=2, column=0) # Place groups frame
        self._msgFrame.grid(row=3, column=0) # Place msg frame
    def _handlePostClicked(self, subject: str, content: str):
        server.send(createPostQuery(self._groups.current()[0], subject, content))
    def _handleLeaveClicked(self, group: str):
        server.send(createLeaveQuery(group))
    def handleGroups(self, groups: list[str]):
        for g in groups:
            self._joinFrame.add(g)
        if "Public" in groups:
            server.send(createJoinQuery("Public", self.userName))
    def handleJoin(self, group: str, name: str):
        if name == self.userName: # we have successfully joined the group
            self._joinFrame.remove(group)
            f = self._groups.add(group)
            if f is not None:
                f.add_user(name)
        else: # someone else joined a group we are in
            frame = self._groups.groups.get(group)
            if frame is not None:
                frame.add_user(name)
    def handleLeave(self, group: str, name: str):
        if name == self.userName:
            self._joinFrame.add(group)
            self._groups.remove(group)
        else:
            frame = self._groups.groups.get(group)
            if frame is not None:
                frame.remove_user(name)
    def handleMessage(self, group: str, msgId: int):
        pass
    def handleView(self, group: str, id: int, sender: str, post_date: datetime, subject: str, content: str):
        pass


class JoinFrame(Frame):
    def __init__(self, parent, groups: list[str], userName: str) -> None:
        Frame.__init__(self, parent)
        self._groups = groups
        self._userName = userName
        self._currentGroup = StringVar()
        self._groupBox = ttk.Combobox(self, textvariable=self._currentGroup, values=self._groups)
        self._joinButton = Button(self, text="Join", command=self._handleJoinClicked)
        self._placeFrames()
    def _placeFrames(self):
        self._groupBox.grid(row=0, column=0)
        self._joinButton.grid(row=0, column=1)
    def _handleJoinClicked(self) -> None:
        group = self._currentGroup.get()
        if group != "":
            q = createJoinQuery(group, self._userName)
            server.send(q)
    def add(self, group: str):
        if group in self._groups:
            return
        self._groups.append(group)
        self._groupBox['values'] = self._groups
    def remove(self, group: str):
        if group not in self._groups:
            return
        self._groups.remove(group)
        self._groupBox['values'] = self._groups
        if group == self._currentGroup.get():
            self._currentGroup.set("")

class GroupsFrame(Frame):
    def __init__(self, parent, onLeave: Callable[[str], None]):
        Frame.__init__(self, parent)
        self._onLeave = onLeave
        self._nb = ttk.Notebook(self)
        self._nb.grid(row=0, column=0)
        self.groups: dict[str, GroupFrame] = {}
    def current(self):
        name = self._nb.tab(self._nb.select(), 'text')
        return name, self.groups[name]
    def add(self, groupName):
        if groupName in self.groups:
            return
        frame = GroupFrame(self._nb, lambda: self._onLeave(groupName))
        self._nb.add(frame, text=groupName)
        self.groups[groupName] = frame
        return frame
    def remove(self, groupName):
        if groupName not in self.groups:
            return
        frame = self.groups[groupName]
        self._nb.forget(frame)
        del self.groups[groupName]

class GroupFrame(Frame):
    def __init__(self, parent, onLeave: Callable[[], None]):
        Frame.__init__(self, parent)
        self._messages: dict[int, tuple[str, datetime, str, str] | None] = {}
        self._currentMsg: int | None = None
        self._users = UsersFrame(self)
        self._messagesFrame = MessagesFrame(self, self._handleMsgSelectionChanged)
        self._details = DetailFrame(self, onLeave)
        self._placeFrames()
    def _placeFrames(self):
        self._users.grid(row=0, column=0)
        self._messagesFrame.grid(row=0, column=1)
        self._details.grid(row=0, column=2)
    def _handleMsgSelectionChanged(self, msgId: int | None):
        self._currentMsg = msgId
    def add_user(self, user: str):
        self._users.add(user)
    def remove_user(self, user: str):
        self._users.remove(user)
    def add_msg(self, id: int):
        self._messages[id] = None
        self._messagesFrame.add(id)
    def add_msg_contents(self, id: int, sender: str, post_date: datetime, subject: str, content: str):
        self._messages[id] = [sender, post_date, subject, content]
    

class UsersFrame(LabelFrame):
    def __init__(self, parent):
        LabelFrame.__init__(self, parent, text="Users")
        self._usersBox = Listbox(self)
        self._scroll = Scrollbar(self)
        # configure scrolling
        self._scroll.config(command=self._usersBox.yview)
        self._usersBox.config(yscrollcommand=self._scroll.set)
        self._placeFrames()
    def _placeFrames(self):
        self._usersBox.pack(side='left', fill='both', expand=True)
        self._scroll.pack(side='right', fill='y')
    def add(self, userName: str):
        items = self._usersBox.get(0, END)
        if userName in items:
            return
        self._usersBox.insert(END, userName)
    def remove(self, userName: str):
        items: list[str] = self._usersBox.get(0, END)
        if userName not in items:
            return
        try:
            index = items.index(userName)
        except ValueError:
            return
        self._usersBox.delete(index)

class MessagesFrame(LabelFrame):
    def __init__(self, parent, onMessageSelectionChanged: Callable[[int | None], None]):
        LabelFrame.__init__(self, parent, text="Messages")
        self._onMessageSelectionChanged = onMessageSelectionChanged
        self._messages: list[str] = []
        # create components
        self._messagesVar = StringVar(value=self._messages)
        self._messagesBox = Listbox(self, selectmode='single', listvariable=self._messagesVar)
        self._scroll = Scrollbar(self)
        self._messagesBox.bind("<<ListboxSelect>>", self._onListboxSelect) # bind selection event
        # configure scrolling
        self._messagesBox.config(yscrollcommand=self._scroll.set)
        self._scroll.config(command=self._messagesBox.yview)
        self._placeFrames() # place frames
    def _onListboxSelect(self, event):
        indices: list[int] = event.widget.curselection()
        if len(indices) <= 0:
            return
        index = indices[0]
        if index:
            id = event.widget.get(index)
            self._onMessageSelectionChanged(int(id))
        else:
            self._onMessageSelectionChanged(None)
    def _placeFrames(self):
        self._messagesBox.pack(side='left', fill='both', expand=True)
        self._scroll.pack(side='right', fill='y')
    def add(self, messageId: str):
        self._messages.append(messageId)
        self._messagesVar.set(",".join(self._messages))


class DetailFrame(Frame):
    def __init__(self, parent, onLeave: Callable[[], None]):
        Frame.__init__(self, parent)
        self._onLeave = onLeave
        self._senderVar = StringVar()
        self._senderLabel = Label(self, text="From: ")
        self._senderEntry = Entry(self, textvariable=self._senderVar, state=['readonly'])

        self._dateVar = StringVar()
        self._dateLabel = Label(self, text="Date: ")
        self._dateEntry = Entry(self, textvariable=self._dateVar, state=['readonly'])

        self._subjectVar = StringVar()
        self._subjectLabel = Label(self, text="Subject: ")
        self._subjectEntry = Entry(self, textvariable=self._subjectVar, state=['readonly'])

        self._content = Text(self, width=20, height=5)
        self._leaveButton = Button(self, text="Leave", command=self._onLeaveClicked)

        self._placeFrames()
    def _placeFrames(self):
        self._senderLabel.grid(row=0, column=0)
        self._senderEntry.grid(row=0, column=1)
        self._dateLabel.grid(row=1, column=0)
        self._subjectLabel.grid(row=2, column=0)
        self._dateEntry.grid(row=1, column=1)
        self._subjectEntry.grid(row=2, column=1)
        self._content.grid(row=3, column=0, columnspan=2)
        self._leaveButton.grid(row=4, column=0, columnspan=2)
    def _onLeaveClicked(self):
        self._onLeave()
    def setSender(self, val: str = ""):
        self._senderVar.set(val)
    def setFrom(self, val: datetime | None = None):
        if val is None:
            self._senderVar.set("")
        else:
            self._senderVar.set(val.strftime("%I:%M:%S %p, %b %d, %Y"))
    def setSubject(self, val: str = ""):
        self._subjectVar.set(val)
    def setContent(self, val: str = ""):
        self._content.delete("1.0", END) # Clear
        self._content.insert(END, val) # Set new

class MessagingFrame(Frame):
    def __init__(self, parent, onPost: Callable[[str, str], None]):
        Frame.__init__(self, parent)
        self._onPost = onPost
        self._subjectVar = StringVar()
        self._subjectLabel = Label(self, text="Subject")
        self._subjectEntry = Entry(self, textvariable=self._subjectVar)
        self._contentVar = StringVar()
        self._contentLabel = Label(self, text="Content")
        self._contentEntry = Entry(self, textvariable=self._contentVar)
        self._postButton = Button(self, text="Post", command=self._onPostClicked)
        self._placeFrames()
    def _placeFrames(self):
        self._subjectLabel.grid(row=0, column=0)
        self._subjectEntry.grid(row=0, column=1)
        self._contentLabel.grid(row=0, column=2)
        self._contentEntry.grid(row=0, column=3)
        self._postButton.grid(row=0, column=4)
    def _onPostClicked(self):
        subject = self._subjectVar.get()
        content = self._contentVar.get()
        if subject == "" or content == "":
            return
        self._onPost(subject, content)
        self._clearEntries()
    def _clearEntries(self):
        self._subjectEntry.delete(0, END)
        self._contentEntry.delete(0, END)

def onResponseReceived(main: MainFrame, response: str):
    print(f'! {response}') # Log the response from the server
    if response.startswith("GROUPS|"):
        groups = parseGroupsMsg(response)
        main.handleGroups(groups)
    elif response.startswith("JOIN|"):
        group, name = parseJoinMsg(response)
        main.handleJoin(group, name)
    elif response.startswith("LEAVE|"):
        group, name = parseLeaveMsg(response)
        main.handleLeave(group, name)
    elif response.startswith("MESSAGE|"):
        group, msgid = parseMessageMsg(response)
        main.handleMessage(group, msgid)
    elif response.startswith("VIEW|"):
        group, id, sender, post_date, subject, content = parseViewMsg(response)
        main.handleView(group, id, sender, post_date, subject, content)

# Define a method to handle the ui connecting
def onConnected():
    userName = conn.getUserName() # fetch the user name from the connection frame
    main = MainFrame(root, userName) # Create the main frame
    server.listen(lambda msg : onResponseReceived(main, msg)) # start listening for server messages
    conn.destroy() # Remove the connection frame
    main.grid(row=0, column=0) # Place the main frame

# Initialize some global variables
server = Server()

root = Tk() # Initialize the GUI
root.title("Client") # set the title

conn = ConnectionFrame(root, onConnected) # create connection frame, with onConnected success handler
conn.grid(row=0, column=0) # place the connection frame in root

# Define a close function when exiting
def onClosing():
    if server.connected:
        server.disconnect() # close the socket
    root.destroy() # close the ui window
root.protocol("WM_DELETE_WINDOW", onClosing) # Register the function handler

root.mainloop()