# server side only facilitates finding other peers & sharing the IP & Port #
import socket
import threading

# Server Configuration
HOST = '0.0.0.0'
PORT = 5050
AUDIO_PORT = 6000  # UDP port every client binds for peer audio
MySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
MySocket.bind((HOST, PORT))
MySocket.listen()

# list of username online in total, and in channel1, and in channel2 -- for listening from multiple clients?
AllUsernames = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", "Juliet", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo", "Sierra", "Tango", "Uniform", "Victor", "Whiskey", "X-Ray", "Yankee", "Zulu"]
AvailableUsernames = AllUsernames.copy()
OnlineUsers = {}
Channels = {
    "Channel 1": {},
    "Channel 2": {}
} # channels are fixed ports btw.

# function handling client requests & identification: Registering and Keeping Track
# alongside broadcasting client IP to facilitate p2p amongst themselves.
def handle_client(conn, addr):
    username = None
    channel = None
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            # print(data)
            msg = data.decode().strip() # removes newlines
            print(msg)
            # messages are formatted with: [TYPE OF MESSAGE] [ARGUMENT] [PORT]
            parts = msg.split()
            if not parts:
                continue
            command = parts[0]

            # when client first connect, they have to choose a username display
            if command == "LOBBY":
                response = "USERNAMES " + " ".join(AvailableUsernames)
                conn.send(response.encode())

            # confirming their selection -- frontend might need to be dynamic.
            # since this is TCP, hopefully transactions are atomic........
            elif command == "REGISTER":
                RequestedName = parts[1]
                if RequestedName not in AvailableUsernames:
                    conn.send(b"REGISTER_FAIL")
                else:
                    username = RequestedName
                    AvailableUsernames.remove(username)
                    OnlineUsers[username] = (addr[0], AUDIO_PORT)
                    conn.send(b"REGISTER_SUCCESS")
            
            # client chooses a channel to communicate in. server shares necessary info for the fun to begin
            # FRONTEND NOTE: DO NOT LET USER GO TO JOIN PAGE WITHOUT REGISTERING A USERNAME...
            elif command == "JOIN":
                if not username:
                    conn.send(b"ERROR Not registered")
                    continue

                channel = " ".join(parts[1:])
                if channel not in Channels:
                    conn.send(b"ERROR Invalid channel")
                    continue

                Channels[channel][username] = OnlineUsers[username]
                PeerStrings = [f"{username}:{ip}:{port}" for username, (ip, port) in Channels[channel].items()] # so looks like: ["Alpha:192.168.1.5:6000", "Bravo:192.168.1.8:6001"] << is ["USERNAME1:IP1:PORT1", "USERNAME2:IP2:PORT2"]
                response = "PEERS " + " ".join(PeerStrings)
                print("DEBUG CHANNEL STATE:", Channels[channel])
                # print(response)
                conn.send(response.encode())

            # client exits channel and is in channel lobby
            elif command == "RETURN":
            # TODO: not connected in client.py or UI.py yet
                Channels[channel].pop(username, None)
                print(f"disconnected from {channel}")
                channel = None
    
    # if any error happens. go here
    except Exception as e:
        print("Error: ", e)
    
    # if client disconnects
    finally:
        print(f"{addr} disconnected")
        if username:
            OnlineUsers.pop(username, None)
            for ch in Channels.values(): # clean sweep
                ch.pop(username, None)
            AvailableUsernames.append(username) # username available to be used again
        conn.close()


def start_server():
    print("Server Listening...")
    while True:
        conn, addr = MySocket.accept()
        print("connected by:", addr)
        # use threading per client
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

start_server()
        