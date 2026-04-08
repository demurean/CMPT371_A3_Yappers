# server side only facilitates finding other peers & sharing the IP & Port #
import socket
import threading

# Server Configuration
HOST = '0.0.0.0'
PORT = 5050
AUDIO_PORT = 6000  # UDP port every client binds for peer audio
MySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
MySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
MySocket.bind((HOST, PORT))
MySocket.listen()

# list of username online in total, and in channel1, and in channel2 -- for listening from multiple clients?
AllUsernames = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", "Juliet", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo", "Sierra", "Tango", "Uniform", "Victor", "Whiskey", "X-Ray", "Yankee", "Zulu"]
AvailableUsernames = AllUsernames.copy()
OnlineUsers = {}
Connections = {}    # username -> TCP conn, for push notifications
UserStatuses = {}   # username -> "away" | "active"
Channels = {
    "Channel 1": {},
    "Channel 2": {}
} # channels are fixed ports btw.

# function handling client requests & identification: Registering and Keeping Track
# alongside broadcasting client IP to facilitate p2p amongst themselves.
def broadcast_channel_counts():
    """Push current channel counts to every connected client."""
    entries = [f"{ch}:{len(members)}" for ch, members in Channels.items()]
    msg = "CHANNEL_COUNT_NOTIFY " + "|".join(entries) + "\n"
    for conn in list(Connections.values()):
        try:
            conn.sendall(msg.encode())
        except Exception:
            pass

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
            if command == "LOBBY_ALL":
                FirstResponse = "ALL_USERNAMES " + " ".join(AllUsernames)
                conn.send(FirstResponse.encode())
            elif command == "LOBBY_AVAIL":
                response = "AVAIL_USERNAMES " + " ".join(AvailableUsernames)
                conn.send(response.encode())

            # confirming their selection -- frontend might need to be dynamic.
            # since this is TCP, hopefully transactions are atomic........
            elif command == "REGISTER":
                RequestedName = parts[1]
                if RequestedName not in AvailableUsernames:
                    conn.send(b"REGISTER_FAIL")
                else:
                    username = RequestedName
                    udp_port = int(parts[2]) if len(parts) > 2 else AUDIO_PORT
                    AvailableUsernames.remove(username)
                    OnlineUsers[username] = (addr[0], udp_port)
                    Connections[username] = conn
                    conn.send(b"REGISTER_SUCCESS")
                    print(f"CURRENTLY ONLINE ({', '.join(OnlineUsers.keys())})")
            
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
                UserStatuses[username] = "active"   # reset status on join
                PeerStrings = [
                    f"{u}:{ip}:{port}:{UserStatuses.get(u, 'active')}"
                    for u, (ip, port) in Channels[channel].items()
                ]
                response = "PEERS " + " ".join(PeerStrings)
                print("DEBUG CHANNEL STATE:", Channels[channel])
                # print(response)
                conn.send(response.encode())

                # notify existing members that a new peer joined
                ip, port = OnlineUsers[username]
                notify = f"JOIN_NOTIFY {username}:{ip}:{port}\n"
                for member in list(Channels[channel]):
                    if member != username and member in Connections:
                        try:
                            Connections[member].sendall(notify.encode())
                        except Exception:
                            pass
                broadcast_channel_counts()

            elif command == "STATUS":
                if len(parts) >= 2 and channel:
                    status = parts[1]  # "away" or "active"
                    UserStatuses[username] = status
                    notify = f"STATUS_NOTIFY {username}:{status}\n"
                    for member in list(Channels[channel]):
                        if member != username and member in Connections:
                            try:
                                Connections[member].sendall(notify.encode())
                            except Exception:
                                pass

            # client exits channel and is in channel lobby
            elif command == "RETURN":
                Channels[channel].pop(username, None)
                UserStatuses.pop(username, None)
                print(f"disconnected from {channel}")
                notify = f"LEAVE_NOTIFY {username}\n"
                for member in list(Channels[channel]):
                    if member in Connections:
                        try:
                            Connections[member].sendall(notify.encode())
                        except Exception:
                            pass
                broadcast_channel_counts()
                channel = None
            
            # if client requests usercount in each channel -- for lobby use
            elif command == "GET_COUNT":
                entries = []
                for ch in Channels:
                    count = len(Channels[ch])
                    entries.append(f"{ch}:{count}")
                CountString = f"CHANNEL_COUNT " + "|".join(entries)
                conn.send(CountString.encode())

                
    
    # if any error happens. go here
    except Exception as e:
        print("Error: ", e)
    
    # if client disconnects
    finally:
        print(f"{addr} disconnected")
        if username:
            Connections.pop(username, None)
            OnlineUsers.pop(username, None)
            UserStatuses.pop(username, None)
            if channel:
                Channels[channel].pop(username, None)
                notify = f"LEAVE_NOTIFY {username}\n"
                for member in list(Channels[channel]):
                    if member in Connections:
                        try:
                            Connections[member].sendall(notify.encode())
                        except Exception:
                            pass
            for ch in Channels.values(): # clean sweep
                ch.pop(username, None)
            AvailableUsernames.append(username) # username available to be used again
            broadcast_channel_counts()
        conn.close()


def start_server():
    print("Server Listening...")
    while True:
        try:
            conn, addr = MySocket.accept()
        except OSError:
            break
        print("connected by:", addr)
        # use threading per client
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()
        