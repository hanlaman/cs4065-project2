import java.io.*;
import java.net.*;

public class BulletinBoardClient {
    private static Socket socket;
    private static BufferedReader in;
    private static PrintWriter out;
    private static BufferedReader userInput;
    private static String username = null;

    public static void main(String[] args) {
        userInput = new BufferedReader(new InputStreamReader(System.in));
        
        while (true) {
            try {
                System.out.println("Welcome to the Bulletin Board System.");
                System.out.println("Type %connect [address] [port] to connect to the server.");
                System.out.println("Type %exit to exit.");
                System.out.print("> ");
                
                String command = userInput.readLine().trim();

                if (command.startsWith("%connect")) {
                    connectToServer(command);
                } else if (command.equals("%exit")) {
                    exit();
                    break;
                } else {
                    System.out.println("Invalid command. Please type %connect [address] [port] to connect.");
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    // Connect to the server
    private static void connectToServer(String command) {
        String[] commandParts = command.split(" ");
        if (commandParts.length < 3) {
            System.out.println("Usage: %connect [address] [port]");
            return;
        }
        String serverAddress = commandParts[1];
        int serverPort = Integer.parseInt(commandParts[2]);

        try {
            socket = new Socket(serverAddress, serverPort);
            in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            out = new PrintWriter(socket.getOutputStream(), true);
            
            System.out.println("Connected to server at " + serverAddress + ":" + serverPort);
            handleUserCommands();
        } catch (IOException e) {
            System.out.println("Unable to connect to the server: " + e.getMessage());
        }
    }

    // Handle the user commands after a successful connection
    private static void handleUserCommands() {
        try {
            while (true) {
                System.out.println("\nEnter a command:");
                System.out.println("%join - Join the message board");
                System.out.println("%post [subject] [message] - Post a message");
                System.out.println("%users - Retrieve a list of users in the group");
                System.out.println("%leave - Leave the group");
                System.out.println("%message [ID] - Retrieve a specific message");
                System.out.println("%exit - Exit the client");
                System.out.print("> ");

                String command = userInput.readLine().trim();
                out.println(command);

                if (command.startsWith("%post")) {
                    handlePost(command);
                } else if (command.equals("%join")) {
                    joinGroup();
                } else if (command.equals("%users")) {
                    listUsers();
                } else if (command.equals("%leave")) {
                    leaveGroup();
                } else if (command.startsWith("%message")) {
                    retrieveMessage(command);
                } else if (command.equals("%exit")) {
                    exit();
                    break;
                } else {
                    System.out.println("Unknown command. Please try again.");
                }

                // Display server's response
                String response = in.readLine();
                while (response != null) {
                    System.out.println(response);
                    if (!in.ready()) {
                        break;
                    }
                    response = in.readLine();
                }
            }
        } catch (IOException e) {
            System.out.println("Error handling user commands: " + e.getMessage());
        }
    }

    // Handle the %post command
    private static void handlePost(String command) throws IOException {
        String[] parts = command.split(" ", 3);
        if (parts.length < 3) {
            System.out.println("Usage: %post [subject] [message]");
            return;
        }
        String subject = parts[1];
        String message = parts[2];

        out.println("%post " + subject + " " + message);
    }

    // Handle the %join command
    private static void joinGroup() throws IOException {
        if (username == null) {
            System.out.println("Enter a unique username to join the group: ");
            username = userInput.readLine();
            out.println(username); // Send username to the server
        }
        out.println("%join");
    }

    // Handle the %users command
    private static void listUsers() {
        out.println("%users");
    }

    // Handle the %leave command
    private static void leaveGroup() throws IOException {
        out.println("%leave");
        username = null;  // Reset username after leaving
    }

    // Handle the %message command
    private static void retrieveMessage(String command) {
        String[] parts = command.split(" ");
        if (parts.length < 2) {
            System.out.println("Usage: %message [message ID]");
            return;
        }
        try {
            int messageId = Integer.parseInt(parts[1]);
            out.println("%message " + messageId);
        } catch (NumberFormatException e) {
            System.out.println("Invalid message ID.");
        }
    }

    // Exit the program and close the connection
    private static void exit() {
        try {
            if (socket != null && !socket.isClosed()) {
                out.println("%exit");
                socket.close();
            }
            System.out.println("Exiting... Goodbye!");
        } catch (IOException e) {
            System.out.println("Error while closing the connection: " + e.getMessage());
        }
    }
}
