import java.io.*;
import java.net.*;
import java.util.*;

public class Server {
    private static final int PORT = 12345;
    private static Set<String> users = new HashSet<>();
    private static Map<String, String> messages = new HashMap<>();
    private static Set<PrintWriter> clientWriters = new HashSet<>();

    public static void main(String[] args) {
        System.out.println("Server is running...");
        
        try (ServerSocket serverSocket = new ServerSocket(PORT)) {
            while (true) {
                new ClientHandler(serverSocket.accept()).start();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static class ClientHandler extends Thread {
        private Socket socket;
        private PrintWriter out;
        private BufferedReader in;
        private String username;

        public ClientHandler(Socket socket) {
            this.socket = socket;
        }

        @Override
        public void run() {
            try {
                in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                out = new PrintWriter(socket.getOutputStream(), true);
                
                // Prompt the client for a username
                out.println("Enter username:");
                username = in.readLine();
                
                // Ensure username is unique
                while (users.contains(username) || username.isEmpty()) {
                    out.println("Username taken or invalid. Enter another username:");
                    username = in.readLine();
                }
                users.add(username);
                System.out.println(username + " has joined.");
                
                // Notify client of users in the group
                out.println("Users: " + users);
                
                // Add client output stream to the set of writers
                synchronized (clientWriters) {
                    clientWriters.add(out);
                }
                
                String message;
                while ((message = in.readLine()) != null) {
                    if (message.startsWith("%join")) {
                        out.println("Joined the group: public");
                    } else if (message.startsWith("%post")) {
                        String[] messageParts = message.split(" ", 3);
                        if (messageParts.length >= 3) {
                            String messageId = UUID.randomUUID().toString();
                            String subject = messageParts[1];
                            String content = messageParts[2];
                            messages.put(messageId, "Subject: " + subject + "\nMessage: " + content);
                            broadcastMessage("Message posted by " + username + ": " + subject);
                        } else {
                            out.println("Invalid post command. Correct usage: %post <subject> <content>");
                        }
                    } else if (message.startsWith("%users")) {
                        out.println("Users in group: " + users);
                    } else if (message.startsWith("%leave")) {
                        users.remove(username);
                        synchronized (clientWriters) {
                            clientWriters.remove(out);
                        }
                        out.println("You have left the group.");
                        broadcastMessage(username + " has left the group.");
                        break;
                    } else if (message.startsWith("%exit")) {
                        out.println("Goodbye!");
                        break;
                    } else {
                        out.println("Unknown command: " + message);
                    }
                }
            } catch (IOException e) {
                e.printStackTrace();
            } finally {
                try {
                    socket.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }

        private void broadcastMessage(String message) {
            synchronized (clientWriters) {
                for (PrintWriter writer : clientWriters) {
                    writer.println(message);
                }
            }
        }
    }
}
