import java.io.*;
import java.net.*;
import java.util.*;
import java.text.*;
import java.util.concurrent.*;

public class BulletinBoardServer {
    private static final int PORT = 12345;
    private static Map<Socket, String> clients = new HashMap<>();
    private static List<Message> messages = new ArrayList<>();
    private static Set<Socket> clientSockets = new HashSet<>();
    private static ExecutorService clientThreads = Executors.newCachedThreadPool();

    public static void main(String[] args) {
        try (ServerSocket serverSocket = new ServerSocket(PORT)) {
            System.out.println("Server started on port " + PORT);
            
            while (true) {
                Socket clientSocket = serverSocket.accept();
                System.out.println("New client connected: " + clientSocket.getRemoteSocketAddress());
                clientThreads.submit(() -> handleClient(clientSocket));
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void handleClient(Socket clientSocket) {
        try (BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
             PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true)) {

            // Step 1: Get the username
            out.println("Enter a unique username to join the group:");
            String username = in.readLine().trim();

            synchronized (clients) {
                while (clients.containsValue(username)) {
                    out.println("Username already taken. Please choose a different username:");
                    username = in.readLine().trim();
                }
                clients.put(clientSocket, username);
                clientSockets.add(clientSocket);
            }

            // Notify other clients about the new user
            broadcastMessage("User " + username + " has joined the group.");
            out.println("Welcome, " + username + "!");
            displayUsers(out);

            // Process client commands
            String command;
            while ((command = in.readLine()) != null) {
                if (command.equals("%exit")) {
                    break;
                } else if (command.equals("%join")) {
                    out.println("You are already in the public group.");
                } else if (command.startsWith("%post")) {
                    handlePost(command, username);
                } else if (command.equals("%users")) {
                    displayUsers(out);
                } else if (command.equals("%leave")) {
                    leaveGroup(clientSocket, out, username);
                    break;
                } else if (command.startsWith("%message")) {
                    retrieveMessage(out, command);
                } else {
                    out.println("Unknown command. Please try again.");
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void handlePost(String command, String sender) {
        String[] parts = command.split(" ", 3);
        if (parts.length < 3) {
            System.out.println("Usage: %post [subject] [message]");
            return;
        }
        String subject = parts[1];
        String body = parts[2];

        Message newMessage = new Message(messages.size() + 1, sender, new Date(), subject, body);
        messages.add(newMessage);
        broadcastMessage("New message posted by " + sender + ": " + subject);
    }

    private static void displayUsers(PrintWriter out) {
        out.println("\nUsers currently in the group:");
        synchronized (clients) {
            for (String username : clients.values()) {
                out.println(username);
            }
        }
    }

    private static void retrieveMessage(PrintWriter out, String command) {
        String[] parts = command.split(" ");
        if (parts.length < 2) {
            out.println("Usage: %message [message ID]");
            return;
        }
        try {
            int messageId = Integer.parseInt(parts[1]);
            if (messageId > 0 && messageId <= messages.size()) {
                out.println(messages.get(messageId - 1).getFormattedMessage());
            } else {
                out.println("Message ID not found.");
            }
        } catch (NumberFormatException e) {
            out.println("Invalid message ID.");
        }
    }

    private static void leaveGroup(Socket clientSocket, PrintWriter out, String username) {
        synchronized (clients) {
            clients.remove(clientSocket);
            clientSockets.remove(clientSocket);
        }
        broadcastMessage("User " + username + " has left the group.");
        out.println("You have left the group.");
    }

    private static void broadcastMessage(String message) {
        synchronized (clientSockets) {
            for (Socket clientSocket : clientSockets) {
                try {
                    PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true);
                    out.println(message);
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    // Message class to store message details
    static class Message {
        private int id;
        private String sender;
        private Date timestamp;
        private String subject;
        private String body;

        public Message(int id, String sender, Date timestamp, String subject, String body) {
            this.id = id;
            this.sender = sender;
            this.timestamp = timestamp;
            this.subject = subject;
            this.body = body;
        }

        public String getFormattedMessage() {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            return String.format("ID: %d, Sender: %s, Date: %s, Subject: %s\n%s",
                    id, sender, sdf.format(timestamp), subject, body);
        }
    }
}
