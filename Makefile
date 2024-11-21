# Makefile for running Java server and Python client

# Variables
JAVA_FILES = Server.java
CLIENT_FILE = client.py
SERVER_CLASS = Server
CLIENT_SCRIPT = client.py
JAVAC = javac
JAVA = java
PYTHON = python3

# Default target: Build everything
all: server client

# Target to compile the Java server
server:
	$(JAVAC) $(JAVA_FILES)

# Target to run the Java server
run_server:
	$(JAVA) $(SERVER_CLASS)

# Target to run the Python client
run_client:
	$(PYTHON) $(CLIENT_SCRIPT)

# Target to run both the server and the client in the background
run_all: run_server & run_client

# Target to clean up compiled Java files
clean:
	rm -f *.class

# Help target
help:
	@echo "Makefile Commands:"
	@echo "  all            - Compile and build both server and client"
	@echo "  server         - Compile the Java server"
	@echo "  run_server     - Run the Java server"
	@echo "  run_client     - Run the Python client"
	@echo "  run_all        - Run both server and client (background)"
	@echo "  clean          - Clean up compiled files"
	@echo "  help           - Show this help message"
