import java.io.*;
import java.net.*;
import java.time.Instant;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.ThreadFactory;

// server class to manage client connections and message boards 
public class Server {
    // factory for creating virtual threads for clients
    public static final ThreadFactory clientThreadFactory = Thread.ofVirtual().factory();

    // predefined message boards available on the server
    public static final Map<String, Board> Groups = Map.ofEntries(
        Map.entry("Public", new Board("Public")),
        Map.entry("Group1", new Board("Group1")),
        Map.entry("Group2", new Board("Group2")),
        Map.entry("Group3", new Board("Group3")),
        Map.entry("Group4", new Board("Group4")),
        Map.entry("Group5", new Board("Group5"))
    );

    // main method to initialize the server and handle client connections
    public static void main(String[] args) {
        try {
            // create a server socket on an available port
            ServerSocket connectionSocket = new ServerSocket(0);
            System.out.println("Waiting for connections on port " + connectionSocket.getLocalPort());
            while (true) { 
                Socket socket = connectionSocket.accept(); // wait for a connection
                System.out.println("New connection from " + socket.getInetAddress().getHostAddress() + ":" + socket.getPort());
                // start a new thread to handle the connected client 
                Thread clientThread = clientThreadFactory.newThread(new Client(socket));
                clientThread.setName("Client-" + socket.getInetAddress().getHostAddress() + ":" + socket.getPort());
                clientThread.start();
            }
        } 
        catch (IOException ioe) {
            ioe.printStackTrace();
        }
    }
}

// client class to handle communication with an individual client 
class Client implements Runnable {
    private final ThreadFactory commandThreadFactory; // factory for creating threads for commands
    private final Object lock = new Object(); // lock for thread synchronization
    public Socket socket;
    private BufferedReader reader; // reader for incoming client messages 
    private PrintWriter writer; // writer for sending messages to client 
    public final Set<Board> boards = new HashSet<>(); // set of boards that the client has joined 

    // constructor initializes client socket and I/O streams
    public Client(Socket socket) {
        this.socket = socket;
        commandThreadFactory = Thread.ofVirtual().factory();
        try {
            this.reader = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            this.writer = new PrintWriter(socket.getOutputStream(), true);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // method to send a message to client 
    public void send(String message) {
        synchronized (this.lock) {
            System.out.println(socket.getInetAddress().getHostAddress() + ":" + socket.getPort() + " < " + message);
            writer.print(message + "\n");
            writer.flush();
        }
    }

    // main loop for handling client messages 
    @Override
    public void run() {
        var threads = new ArrayList<Thread>();
        while (true) { 
            String msg;
            try {
                // read message from client 
                msg = reader.readLine();
            } catch (IOException e) {
                break;
            }
            if (msg == null) break;
            System.out.println(socket.getInetAddress().getHostAddress() + ":" + socket.getPort() + " ? " + msg);
            if (msg.equals("EXIT")) break;
            Thread t = handleMsg(msg);
            if (t != null) threads.add(t);
        }
        
        // create commands to leave all boards
        for (var board : boards) {
            Thread t = handleMsg("LEAVE|" + board.boardName);
            if (t != null) threads.add(t);
        }

        // join all msg threads if still active
        for (var thread : threads) {
            try {
                thread.join();
            } catch (InterruptedException e) {
                break;
            }
        }

        System.out.println("Closing connection from " + socket.getInetAddress().getHostAddress() + ":" + socket.getPort());
        try {
            socket.close();
        } catch (IOException e) { }
    }

    // handle message from client by creating a new command thread 
    private Thread handleMsg(String msg) {
        var thread = commandThreadFactory.newThread(new Command(this, msg));
        if (thread == null) return null;
        thread.setName(msg);
        thread.start();
        return thread;
    }
}

// command class to execute client commands 
class Command implements Runnable {
    private final Client caller; // reference to the client issuing the command
    private final String text; // command text 
    
    public Command(Client caller, String text) {
        this.caller = caller;
        this.text = text;
    }

    // executes the command based on its type 
    @Override
    public void run() {
        if (text.startsWith("GROUPS")) {
            runGroups();
        } 
        else if (text.startsWith("JOIN|")) {
            var parts = text.split("\\|");
            var group = parts[1];
            var nameInGroup = parts[2];
            runJoinGroup(group, nameInGroup);
        }
        else if (text.startsWith("POST|")) {
            var parts = text.split("\\|");
            var group = parts[1];
            var subject = parts[2];
            var content = parts[3];
            runPost(group, subject, content);
        }
        else if (text.startsWith("LEAVE|")) {
            var parts = text.split("\\|");
            var group = parts[1];
            runLeave(group);
        }
        else if (text.startsWith("VIEW|")) {
            var parts = text.split("\\|");
            var group = parts[1];
            var id = parts[2];
            runView(group, Integer.parseUnsignedInt(id));
        }
        else if (text.startsWith("PING")) {
            caller.send("PING");
        }
    }

    // handles the GROUPS query 
    private void runGroups() {
        var groupNames = Server.Groups.keySet();
        String response = "GROUPS"; // construct group response
        for (var groupName : groupNames) {
            response += "|" + groupName; // append all group names
        }
        caller.send(response);
    }

    // handles the JOIN query 
    private void runJoinGroup(String group, String name) {
        if (!Server.Groups.containsKey(group)) return;
        var board = Server.Groups.get(group);
        if (caller.boards.contains(board)) return;

        board.Join(caller, name); // join the caller client to the board
        caller.boards.add(board); // add the board to the callers memory
        caller.send("JOIN|" + group + "|" + name); // notify caller they've joined the group

        // send last two messages back
        var ids = board.GetLastTwoMessageIds();
        if (ids.length > 0) caller.send("MESSAGE|" + group + "|" + Integer.toUnsignedString(ids[0]));
        if (ids.length > 1) caller.send("MESSAGE|" + group + "|" + Integer.toUnsignedString(ids[1]));

        // notify client of all users in group
        for (var user : board.Users()) {
            if (!name.equals(user))
                caller.send("JOIN|" + group + "|" + user);
        }
    }

    // handles the POST query 
    private void runPost(String group, String subject, String content) {
        if (!Server.Groups.containsKey(group)) return;
        var board = Server.Groups.get(group);

        board.Post(caller, subject, content); // post to the board
    }

    // handles the LEAVE query 
    private void runLeave(String group) {
        if (!Server.Groups.containsKey(group)) return;
        var board = Server.Groups.get(group);
        if (!caller.boards.contains(board)) return;

        board.Leave(caller); // leave the board
        caller.boards.remove(board); // stop tracking the board on the client
    }

    // handles the VIEW query 
    private void runView(String group, Integer id) {
        if (!Server.Groups.containsKey(group)) return;
        var board = Server.Groups.get(group);
        if (!caller.boards.contains(board)) return;
        if (!board.Messages.containsKey(id)) return;
        var msg = board.Messages.get(id); // get the message

        // send contents to the client
        caller.send("VIEW|" + group + "|" + Integer.toUnsignedString(id) + "|" + msg.Sender + "|" + DateTimeFormatter.ISO_INSTANT.format(msg.PostDate) + "|" + msg.Subject + "|" + msg.Content);
    }
}

// message class represents a single message in a board 
class Message {
    public final Instant PostDate;
    public final String Sender;
    public final String Subject;
    public final String Content;

    public Message(String sender, Instant postDate, String subject, String content) {
        PostDate = postDate;
        Sender = sender;
        Subject = subject;
        Content = content;
    }
}

// board class represents a message board where clients can post messages 
class Board {
    public final String boardName;
    private final Random rnd; // random number generator for message IDs
    public final Map<Integer, Message> Messages = new HashMap<>();
    private final Map<Client, String> clients = new HashMap<>();

    public Board(String name) {
        rnd = new Random();
        boardName = name;
    }

    // adds a client to the board 
    public void Join(Client client, String name) {
        synchronized (clients) {
            for (var other : clients.keySet()) {
                other.send("JOIN|" + boardName + "|" + name); // notify all existing board clients of a join
            }
            clients.put(client, name); // track new client
        }
    }

    // removes a client from the board 
    public void Leave(Client client) {
        if (!clients.containsKey(client)) return;
        synchronized (clients) {
            var name = clients.get(client);
            for (var other : clients.keySet()) {
                other.send("LEAVE|" + boardName + "|" + name); // notify all board client of a leave
            }
            clients.remove(client); // stop tracking client on board
        }
    }

    // posts a message to the board 
    public void Post(Client client, String subject, String content) {
        if (!clients.containsKey(client)) return;
        var id = rnd.nextInt(); // generate new message id
        var message = new Message(clients.get(client), Instant.now(), subject, content); // create new message structure
        Messages.put(id, message);

        // notify others of a new message
        synchronized (clients) {
            for (var other : clients.entrySet()) {
                other.getKey().send("MESSAGE|" + boardName + "|" + Integer.toUnsignedString(id));
            }
        }
    }

    public Collection<String> Users() {
        return clients.values(); // get list of usernames
    }

    // gets the last two message IDs from the board 
    public Integer[] GetLastTwoMessageIds() {
        var messages = new ArrayList<>(Messages.entrySet());
        Collections.sort(messages, (left, right) -> right.getValue().PostDate.compareTo(left.getValue().PostDate)); // sort reversed by post date
        return messages
            .stream()
            .limit(2) // get most recent two
            .sorted((left, right) -> left.getValue().PostDate.compareTo(right.getValue().PostDate)) // sort ascending post date
            .map(e -> e.getKey()) // get the message ids
            .toArray(Integer[]::new); // send into an array
    }
}
