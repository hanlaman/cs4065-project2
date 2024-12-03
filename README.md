# Hannah Laman, Spencer Will, Soham Vakani
## Overview
This project implements a client-server bulletin board system using sockets. The system allows users to connect via a terminal or GUI client, join public or private groups, post and read messages, and manage group memberships. The project is divided into two parts:

#### Part 1: Public Message Board
- All clients belong to a single public group where they can interact and view the latest two messages upon joining.


#### Part 2: Multiple Private Message Boards
- Users can join one or more private groups, each with its own set of members and messages. Messages and user lists are isolated per group.

The system supports Java-based server implementation and Python-based client applications.

## Features
#### Server
- Multithreading: Handles multiple client connections simultaneously.
- Group Management: Supports public and private groups.
- Message Storage: Maintains and retrieves posted messages with metadata.
- Notifications: Broadcasts user join/leave events to group members.
- Protocol Support: Implements a custom text-based protocol for client-server communication.
#### Client
- Connection Management: Connects to the server using a specified host and port.
- Message Handling: Supports posting, retrieving, and viewing messages.
- Group Features: Joins public/private groups, retrieves user lists, and leaves groups.
- GUI and CLI Options: Provides both a GUI (using Python's tkinter) and CLI-based interface.

## Prerequisites
#### Server
- Java Development Kit (JDK) 17 or higher
#### Client
- Python 3.10 or higher
- Required Python libraries:
  - tkinter (for GUI)
  - threading

## Setup and Installation
*Please make sure that you are in the correct directory*.
#### Server
- Compile the server code:
  - `javac Server.java`
- Run the server:
  - `java Server`
- The server will display the port number it is listening on.
#### Client
- Install Python and dependencies.
- Run the GUI client:
  - `python client.py`
- The GUI should open in a new window. It will prompt you with a username, host, and port.
- Please choose any username. The host is localhost, and the port will be given to you in the first terminal. 
