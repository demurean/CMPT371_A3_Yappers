# client side connects to server to share IP and receive others' IP (IN SAME NETWORK)
# client then proceeds to broadcast to other clients audio data

import socket

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
    FORMAT = pyaudio.paInt16
except ImportError:
    PYAUDIO_AVAILABLE = False
    FORMAT = None
    print("Warning: pyaudio not installed. Run: pip install pyaudio")

# Audio / UDP constants
CHUNK      = 1024
CHANNELS   = 1
RATE       = 44100
AUDIO_PORT = 6000   # UDP port all clients listen on for peer audio

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5050
Username = None
UDP_PORT = 0

## 1. CLIENT ESTABLISHING CONNECTION TO SERVER + Choosing Username
def GetAllUsernames(s):
    s.sendall(b'LOBBY_ALL')  
    FirstData = s.recv(1024).decode().strip()
    FirstParts = FirstData.split()
    if FirstParts[0] == "ALL_USERNAMES":
        AllUsernames = FirstParts[1:]
        return AllUsernames
    else:
        return []
    
def GetAvailableUsernames(s):
    s.sendall(b'LOBBY_AVAIL')  
    data = s.recv(1024).decode().strip()
    parts = data.split()
    if parts[0] == "AVAIL_USERNAMES":
        usernames = sorted(parts[1:]) # list always in alphabetical order
        return usernames
    else:
        return []

def RegisterUsername(s, username, udp_port):
    message = f"REGISTER {username} {udp_port}"
    s.sendall(message.encode())
    response = s.recv(1024).decode().strip()
    return response # REGISTER_SUCCESS or REGISTER_FAIL

def JoinChannel(s, channel, myUsername):
    message = f"JOIN {channel}"
    s.sendall(message.encode())
    response = s.recv(1024).decode().strip()
    parts = response.split()
    peers = {}
    statuses = {}

    if parts[0] == "PEERS":
        for peer_str in parts[1:]:
            fields = peer_str.rsplit(":", 3)
            if len(fields) == 4:
                username, ip, port, status = fields
            else:
                username, ip, port = peer_str.rsplit(":", 2)
                status = "active"
            if username == myUsername:
                continue
            peers[username] = (ip, int(port))
            statuses[username] = status
    return peers, statuses

def GetUserCountperChannel(s):
    message = f"GET_COUNT"
    s.sendall(message.encode())

    ### there's a bug that fails on this function due to runtime error
    # plan to move to _handle_push in clientUI.py

    response = s.recv(1024).decode().strip()
    argument, payload = response.split(" ", 1)
    CountperChannel = {}

    if argument == "CHANNEL_COUNT":
        entries = payload.split("|")
        for entry in entries:
            ChannelName, ChannelCount = entry.rsplit(":", 1)
            CountperChannel[ChannelName] = ChannelCount
    return CountperChannel

# def start_app():
#     print("starting the application...")
#     # SERVER_HOST = '127.0.0.1'
#     # SERVER_PORT = 5050
#     SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     SERVER_SOCKET.connect((SERVER_HOST,SERVER_PORT))

## 2. AUDIO — P2P via UDP

def setup_udp():
    """Create and bind the UDP socket this client listens on for incoming audio.
    Binds to port 0 so the OS assigns a unique port — required when multiple
    clients run on the same machine (avoids port-6000 collision)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))   # OS picks a free port
    sock.settimeout(1.0)
    return sock

def send_audio_loop(record_stream, udp_sock, peers, username, is_talking_flag, on_chunk=None):
    """
    Reads mic chunks from record_stream and UDP-sends to every peer.
    Runs in its own thread while PTT is held.
    peers: dict  {peer_username: (ip_str, port_int)}
    is_talking_flag: threading.Event -> cleared by caller to stop the loop
    on_chunk(audio_pcm): optional callback for waveform visualisation
    """
    while is_talking_flag.is_set() and record_stream:
        try:
            audio = record_stream.read(CHUNK, exception_on_overflow=False)
            if on_chunk:
                on_chunk(audio)
            header = username.encode().ljust(16)   # fixed 16-byte sender header
            packet = header + audio
            for _peer, (ip, port) in peers.items():
                udp_sock.sendto(packet, (ip, port))
        except Exception as e:
            print(f"send_audio error: {e}")
            break

def receive_audio_loop(udp_sock, playback_stream, running_flag, on_packet):
    """
    Continuously receives UDP audio packets and plays them back.
    running_flag: threading.Event -> cleared by caller to stop the loop
    on_packet(sender, audio_pcm): callback so the GUI can update status circles / waveform
    """
    if playback_stream is None:
        print("WARNING: receive_audio_loop — playback_stream is None, no audio will play")
    while running_flag.is_set():
        try:
            packet, _ = udp_sock.recvfrom(16 + CHUNK * 2)
            if len(packet) < 17:
                continue
            sender    = packet[:16].decode(errors='ignore').strip()
            audio_pcm = packet[16:]
            if on_packet:
                on_packet(sender, audio_pcm)
        except socket.timeout:
            continue
        except Exception as e:
            if running_flag.is_set():
                print(f"receive_audio error: {e}")
            continue
        if playback_stream and audio_pcm:
            try:
                playback_stream.write(audio_pcm)
            except Exception as e:
                print(f"playback write error: {e}")

# order of execution:
# start_app() begins, initiates session to server
# THEN the core app can take place
# NOTE: start_app() not called here — clientUI.py drives the client side app now