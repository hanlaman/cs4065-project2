# Makefile for Bulletin Board System

# Java compiler
JAVAC = javac

# Directories
SRC_DIR = src
BIN_DIR = bin

# Java files to compile
SOURCES = $(SRC_DIR)/BulletinBoardServer.java $(SRC_DIR)/BulletinBoardClient.java
CLASSES = $(BIN_DIR)/BulletinBoardServer.class $(BIN_DIR)/BulletinBoardClient.class

# Compilation rule
$(CLASSES): $(SOURCES)
	@mkdir -p $(BIN_DIR)
	$(JAVAC) -d $(BIN_DIR) $(SOURCES)

# Run the server
run-server: $(CLASSES)
	@java -cp $(BIN_DIR) BulletinBoardServer

# Run the client
run-client: $(CLASSES)
	@java -cp $(BIN_DIR) BulletinBoardClient

# Clean up class files
clean:
	rm -rf $(BIN_DIR)
