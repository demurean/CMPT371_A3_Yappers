# client side connects to server to share IP and receive others' IP (IN SAME NETWORK)
# client then proceeds to broadcast to other clients audio data
import socket
import sys

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5050
Username = None

## 1. CLIENT ESTABLISHING CONNECTION TO SERVER + Choosing Username
def lobby(s):
    s.sendall(b'LOBBY')
    data = s.recv(1024).decode().strip()
    parts = data.split()
    UsernameList = []
    if parts[0] == "USERNAMES":
        UsernameList = parts[1:]
        print('Received', UsernameList)
        Username = input("Choose a username from the list: ")
        # no input error protection since this is going to be drop down list
        message = f"REGISTER {Username}"
        s.sendall(message.encode())
        response = s.recv(1024).decode().strip()
        print("Server:", response)

def channel_lobby(s):
    print("A. Channel 1 \nB. Channel 2")
    answer = input("Select Channel letter to join in(A or B) ")
    # ^^ since we're going to be GUI, no edge case protection here
    if answer == "A":
        Channel = "Channel1"
    elif answer == "B":
        Channel = "Channel2"
    message = f"JOIN {Channel}"
    s.sendall(message.encode())
    response = s.recv(1024).decode().strip()
    print("Server:", response)

def start_app():
    print("starting the application...")
    # SERVER_HOST = '127.0.0.1'
    # SERVER_PORT = 5050
    SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SERVER_SOCKET.connect((SERVER_HOST,SERVER_PORT))
    lobby(SERVER_SOCKET)
    channel_lobby(SERVER_SOCKET)

start_app()
# order of execution:
# start_app() begins, initiates session to server
# THEN the core app can take place