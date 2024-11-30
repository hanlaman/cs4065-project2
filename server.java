import java.io.*;
import java.net.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.ThreadFactory;

public class Server {
    public static final ThreadFactory clientThreadFactory = Thread.ofVirtual().factory();

    public static final Map<String, Board> Groups = Map.ofEntries(
        Map.entry("Public", new Board("Public")),
        Map.entry("Group1", new Board("Group1")),
        Map.entry("Group2", new Board("Group2")),
        Map.entry("Group3", new Board("Group3")),
        Map.entry("Group4", new Board("Group4")),
        Map.entry("Group5", new Board("Group5"))
    );

    public static void main(String[] args) {
        try {
            ServerSocket connectionSocket = new ServerSocket(0);
            System.out.println("Waiting for connections on port " + connectionSocket.getLocalPort());
            while (true) { 
                Socket socket = connectionSocket.accept(); // wait for a connection
                System.out.println("New connection from " + socket.getInetAddress().getHostAddress() + ":" + socket.getPort());
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

class Client implements Runnable {
    private final ThreadFactory commandThreadFactory;
    private final Object lock = new Object();
    public Socket socket;
    private BufferedReader reader;
    private PrintWriter writer;
    public final Set<Board> boards = new HashSet<>();
    
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

    public void send(String message) {
        synchronized (this.lock) {
            System.out.println(socket.getInetAddress().getHostAddress() + ":" + socket.getPort() + " < " + message);
            writer.print(message + "\n");
            writer.flush();
        }
    }

    @Override
    public void run() {
        var threads = new ArrayList<Thread>();
        while (true) { 
            String msg;
            try {
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

    private Thread handleMsg(String msg) {
        var thread = commandThreadFactory.newThread(new Command(this, msg));
        if (thread == null) return null;
        thread.setName(msg);
        thread.start();
        return thread;
    }
}

class Command implements Runnable {
    private final Client caller;
    private final String text;
    
    public Command(Client caller, String text) {
        this.caller = caller;
        this.text = text;
    }

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

    private void runGroups() {
        var groupNames = Server.Groups.keySet();
        String response = "GROUPS";
        for (var groupName : groupNames) {
            response += "|" + groupName;
        }
        caller.send(response);
    }

    private void runJoinGroup(String group, String name) {
        if (!Server.Groups.containsKey(group)) return;
        var board = Server.Groups.get(group);
        if (caller.boards.contains(board)) return;

        board.Join(caller, name);
        caller.boards.add(board);
        caller.send("JOIN|" + group + "|" + name);

        // send last two messages back
        var ids = board.GetLastTwoMessageIds();
        if (ids.length > 0) caller.send("MESSAGE|" + group + "|" + Integer.toUnsignedString(ids[0]));
        if (ids.length > 1) caller.send("MESSAGE|" + group + "|" + Integer.toUnsignedString(ids[1]));

        // send all users in group
        for (var user : board.Users()) {
            if (!name.equals(user))
                caller.send("JOIN|" + group + "|" + user);
        }
    }

    private void runPost(String group, String subject, String content) {
        if (!Server.Groups.containsKey(group)) return;
        var board = Server.Groups.get(group);

        board.Post(caller, subject, content);
    }

    private void runLeave(String group) {
        if (!Server.Groups.containsKey(group)) return;
        var board = Server.Groups.get(group);
        if (!caller.boards.contains(board)) return;

        board.Leave(caller);
        caller.boards.remove(board);
    }

    private void runView(String group, Integer id) {
        if (!Server.Groups.containsKey(group)) return;
        var board = Server.Groups.get(group);
        if (!caller.boards.contains(board)) return;
        if (!board.Messages.containsKey(id)) return;
        var msg = board.Messages.get(id);

        caller.send("VIEW|" + group + "|" + Integer.toUnsignedString(id) + "|" + msg.Sender + "|" + msg.PostDate.format(DateTimeFormatter.ISO_DATE_TIME) + "|" + msg.Subject + "|" + msg.Content);
    }
}

class Message {
    public final LocalDateTime PostDate;
    public final String Sender;
    public final String Subject;
    public final String Content;

    public Message(String sender, LocalDateTime postDate, String subject, String content) {
        PostDate = postDate;
        Sender = sender;
        Subject = subject;
        Content = content;
    }
}

class Board {
    public final String boardName;
    private final Random rnd;
    public final Map<Integer, Message> Messages = new HashMap<>();
    private final Map<Client, String> clients = new HashMap<>();

    public Board(String name) {
        rnd = new Random();
        boardName = name;
    }

    public void Join(Client client, String name) {
        synchronized (clients) {
            for (var other : clients.keySet()) {
                other.send("JOIN|" + boardName + "|" + name);
            }
            clients.put(client, name);
        }
    }

    public void Leave(Client client) {
        if (!clients.containsKey(client)) return;
        synchronized (clients) {
            var name = clients.get(client);
            for (var other : clients.keySet()) {
                other.send("LEAVE|" + boardName + "|" + name);
            }
            clients.remove(client);
        }
    }

    public void Post(Client client, String subject, String content) {
        if (!clients.containsKey(client)) return;
        var id = rnd.nextInt();
        var message = new Message(clients.get(client), LocalDateTime.now(), subject, content);
        Messages.put(id, message);

        // notify others of a new message
        synchronized (clients) {
            for (var other : clients.entrySet()) {
                other.getKey().send("MESSAGE|" + boardName + "|" + Integer.toUnsignedString(id));
            }
        }
    }

    public Collection<String> Users() {
        return clients.values();
    }

    public Integer[] GetLastTwoMessageIds() {
        var messages = new ArrayList<>(Messages.entrySet());
        Collections.sort(messages, (left, right) -> right.getValue().PostDate.compareTo(left.getValue().PostDate)); // sort reversed
        return messages
            .stream()
            .limit(2)
            .sorted((left, right) -> left.getValue().PostDate.compareTo(right.getValue().PostDate))
            .map(e -> e.getKey())
            .toArray(Integer[]::new);
    }
}