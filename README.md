# Hannah Laman, Spencer Will, Soham Vakani
## Overview
This project implements a client-server bulletin board system using sockets. The system allows users to connect via a terminal or GUI client, join public or private groups, post and read messages, and manage group memberships. The project is divided into two parts:

#### Part 1: Public Message Board
- All clients belong to a single public group where they can interact and view the latest two messages upon joining.


#### Part 2: Multiple Private Message Boards
- Users can join one or more private groups, each with its own set of members and messages. Messages and user lists are isolated per group.

The system supports Java-based server implementation and Python-based client applications.

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
- Enter a username of your choice, put "localhost" for host and then input the port that the terminal displayed after you setup the server
- You can now post messages using the GUI and also look at users and join users from the top tab. 
- Open a new instance of the client using the terminal to add multiple users to a group

## Issues we faced
- We faced some issues with the GUI setup and getting all the windows in the right spot and displaying the output of the messages correctly. 
- After looking into more documentation of tkinter we figured out how to get a good GUI that works with all the functions and also display the messages
- We had a parsing error in python during our test runs but this was fixed by updating to the latest version of python 
- Also faced some issues with Date Time for the posted messages but fixed this with some minor changes in code to fix the formatting. 



