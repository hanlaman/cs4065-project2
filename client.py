import socket
import sys

class BulletinBoardClient:
    def __init__(self, host, port):
        self.server_host = host
        self.server_port = port
        self.client_socket = None
        self.username = None

    # Connect to the server
    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_host, self.server_port))
            print("Connected to the server at {}:{}.".format(self.server_host, self.server_port))
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            sys.exit(1)

    # Send a message to the server
    def send_message(self, message):
        try:
            self.client_socket.sendall(message.encode('utf-8'))
            response = self.client_socket.recv(1024).decode('utf-8')
            print(f"Server response: {response}")
        except Exception as e:
            print(f"Error sending message: {e}")

    # Handle user interaction
    def start(self):
        print("Welcome to the Bulletin Board System!")
        self.username = input("Enter your username: ")

        self.connect()

        while True:
            print("\nEnter a command:")
            print("%join <group_name> - Join a group")
            print("%post <subject> <content> - Post a message")
            print("%users - View list of users in the group")
            print("%leave - Leave the group")
            print("%exit - Exit the client")
            
            command = input("Command: ").strip()

            if command.startswith("%join"):
                group_name = command.split()[1] if len(command.split()) > 1 else None
                if group_name:
                    self.send_message(f"JOIN {self.username} {group_name}")
                else:
                    print("Please specify the group name to join.")
            
            elif command.startswith("%post"):
                parts = command.split(' ', 2)
                if len(parts) > 2:
                    subject = parts[1]
                    content = parts[2]
                    self.send_message(f"POST {self.username} {subject} {content}")
                else:
                    print("Please specify the subject and content for the post.")
            
            elif command == "%users":
                self.send_message("USERS")
            
            elif command == "%leave":
                self.send_message(f"LEAVE {self.username}")
                print("You have left the group.")
                break
            
            elif command == "%exit":
                self.send_message(f"EXIT {self.username}")
                print("Exiting the client...")
                break
            
            else:
                print("Unknown command. Try again.")

        self.client_socket.close()

# Main entry point
if __name__ == "__main__":
    host = input("Enter the server address: ")
    port = int(input("Enter the server port: "))
    client = BulletinBoardClient(host, port)
    client.start()
