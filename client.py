# client side connects to server to share IP and receive others' IP (IN SAME NETWORK)
# client then proceeds to broadcast to other clients audio data
import socket
import sys

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5050

## 1. CLIENT ESTABLISHING CONNECTION TO SERVER
def lobby(s):
    s.sendall(b'LOBBY')
    data = s.recv(1024).decode().strip()
    parts = data.split()
    UsernameList = []
    if parts[0] == "USERNAMES":
        UsernameList = parts[1:]
        print('Received', UsernameList)
        ChosenUsername = input("Choose a username from the list: ")
        message = f"REGISTER {ChosenUsername}"
        s.sendall(message.encode())
        response = s.recv(1024).decode().strip()
        print("Server:", response) 

def start_app():
    print("starting the application...")
    # SERVER_HOST = '127.0.0.1'
    # SERVER_PORT = 5050
    SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SERVER_SOCKET.connect((SERVER_HOST,SERVER_PORT))
    while True:
        try: # using this structure so client socket doesn't close in waiting for server
            lobby(SERVER_SOCKET)

        except Exception as e:
            print("Client error:", e)
            break
        

start_app()
# order of execution:
# start_app() begins, initiates session to server
# THEN the core app can take place