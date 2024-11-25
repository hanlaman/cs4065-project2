import java.io.*;
import java.net.*;
import java.util.*;

public class Server {
    public static final Map<String, Board> Groups = Map.ofEntries(
        Map.entry("Public", new Board()),
        Map.entry("Group1", new Board()),
        Map.entry("Group2", new Board()),
        Map.entry("Group3", new Board()),
        Map.entry("Group4", new Board()),
        Map.entry("Group5", new Board())
    );

    public static void main(String[] args) {
        try {
            ServerSocket connectionSocket = new ServerSocket(0);
            System.out.println("Waiting for connections on port " + connectionSocket.getLocalPort());
            while (true) { 
                Socket socket = connectionSocket.accept(); // wait for a connection
                System.out.println("New connection from " + socket.getInetAddress().getHostAddress() + ":" + socket.getPort());
                Thread.startVirtualThread(new Client(socket));
            }
        } 
        catch (IOException ioe) {
            ioe.printStackTrace();
        }
    }
}

class Client implements Runnable {
    public Socket socket;
    private BufferedReader reader;
    private PrintWriter writer;
    
    public Client(Socket socket) {
        this.socket = socket;
        try {
            this.reader = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            this.writer = new PrintWriter(socket.getOutputStream(), true);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void send(String message) {
        writer.print(message + "\n");
        writer.flush();
    }

    @Override
    public void run() {
        String msg;
        try {
            while ((msg = reader.readLine()) != null) {
                fireOffCmdHandler(msg);
            }
            socket.close();
        } catch (IOException e) {
            System.out.println("An error occurred");
        }
    }

    private void fireOffCmdHandler(String msg) {
        Thread.startVirtualThread(new Command(this, msg));
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
        // handle various commands here
        if (text.startsWith("GROUPS|")) {
            runGroups();
        } else if (text.startsWith("PING")) {
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
}

class Message {
    public final Date PostDate;
    public final String Sender;
    public final String Subject;
    public final String Content;

    public Message(String sender, Date postDate, String subject, String content) {
        PostDate = postDate;
        Sender = sender;
        Subject = subject;
        Content = content;
    }
}

class Board {
    public final Map<UUID, Message> Messages = new HashMap<>();
    private final Map<String, Client> clients = new HashMap<>();

    public Board() { }
}