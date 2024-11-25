import java.io.*;
import java.net.*;
import java.util.*;

public class Server {
    private static final Board publicBoard = new Board("public");
    private static final Set<Board> privateBoards = new HashSet<>();

    public static void main(String[] args) {
        try {
            ServerSocket connectionSocket = new ServerSocket(0);
            System.out.println("Waiting for connections on port " + connectionSocket.getLocalPort());
            while (true) { 
                Socket socket = connectionSocket.accept(); // wait for a connection
                System.out.println("New connection from " + socket.getInetAddress().getHostAddress() + ":" + socket.getPort());
                Thread.ofPlatform().start(new Client(socket)); // start a new thread to handle the connection
            }
        } 
        catch (IOException ioe) {
            ioe.printStackTrace();
        }
    }

    private static class Message {
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

    private static class Board {
        public final String Name;
        public final Map<UUID, Message> Messages = new HashMap<>();
        private final Set<Client> clients = new HashSet<>();

        public Board(String name) {
            Name = name;
        }

        public Set<String> UserNames() {
            var userNames = new HashSet<String>(clients.size());
            synchronized (clients) {
                for (var client : clients) {
                    userNames.add(client.userName);
                }
            }
            return userNames;
        }

        public void Join(Client client) {
            clients.add(client);
            Broadcast("JOIN [" + Name + "] " + client.userName);
        }

        public void Post(Client sender, String subject, String content) {
            var message = new Message(sender.userName, new Date(), subject, content);
            var id = UUID.randomUUID();
            Messages.put(id, message);
            Broadcast("POST [" + Name + "] " + "{  }");
        }

        public void Leave(Client client) {
            clients.remove(client);
            Broadcast("LEAVE [" + Name + "] " + client.userName);
        }

        private void Broadcast(String message) {
            synchronized (clients) {
                for (var client : clients) {
                    client.send(message);
                }
            }
        }
    }

    private static class Client implements Runnable {
        public Socket socket;
        public String userName = null;
        
        public Client(Socket socket) {
            this.socket = socket;
        }

        public void send(String message) {
            try {
                var writer = new PrintWriter(socket.getOutputStream(), true);
                writer.println(message);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        @Override
        public void run() {
            try {
                listen();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        private void listen() throws IOException {
            var reader = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            var msg = reader.readLine();
            send(msg);
        }
    }
}
