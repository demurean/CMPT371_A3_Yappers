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
def GetAvailableUsernames(s):
    s.sendall(b'LOBBY')
    data = s.recv(1024).decode().strip()
    parts = data.split()
    if parts[0] == "USERNAMES":
        # TODO: put alphabetical order for the parts 
        return parts[1:]
    else:
        return []

def RegisterUsername(s, username):
    message = f"REGISTER {username}"
    s.sendall(message.encode())
    response = s.recv(1024).decode().strip()
    return response # REGISTER_SUCCESS or REGISTER_FAIL

def JoinChannel(s, channel):
    message = f"JOIN {channel}"
    s.sendall(message.encode())
    response = s.recv(1024).decode().strip()
    parts = response.split()
    peers = {}

    if parts[0] == "PEERS":
        for peer_str in parts[1:]:
            username, ip, port = peer_str.rsplit(":", 2)
            peers[username] = (ip, int(port)) 
    return peers

def GetUserCountperChannel(s):
    message = f"GET_COUNT"
    s.sendall(message.encode())
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
    """Create and bind the UDP socket this client listens on for incoming audio."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', AUDIO_PORT))
    sock.settimeout(1.0)
    # UDP_PORT = sock.getsockname()[1]
    # print(UDP_PORT)
    return sock

def send_audio_loop(record_stream, udp_sock, peers, username, is_talking_flag):
    """
    Reads mic chunks from record_stream and UDP-sends to every peer.
    Runs in its own thread while PTT is held.
    peers: dict  {peer_username: (ip_str, port_int)}
    is_talking_flag: threading.Event -> cleared by caller to stop the loop
    """
    while is_talking_flag.is_set() and record_stream:
        try:
            audio = record_stream.read(CHUNK, exception_on_overflow=False)
            header = username.encode().ljust(16)   # fixed 16-byte sender header
            packet = header + audio
            for _peer, (ip, _port) in peers.items():
                udp_sock.sendto(packet, (ip, AUDIO_PORT))
        except Exception as e:
            print(f"send_audio error: {e}")
            break

def receive_audio_loop(udp_sock, playback_stream, running_flag, on_packet):
    """
    Continuously receives UDP audio packets and plays them back.
    running_flag: threading.Event -> cleared by caller to stop the loop
    on_packet(sender_username): callback so the GUI can update status circles
    """
    while running_flag.is_set():
        try:
            packet, _ = udp_sock.recvfrom(16 + CHUNK * 2)
            if len(packet) < 17:
                continue
            sender    = packet[:16].decode(errors='ignore').strip()
            audio_pcm = packet[16:]
            if on_packet:
                on_packet(sender)
            if playback_stream and audio_pcm:
                playback_stream.write(audio_pcm)
        except socket.timeout:
            continue
        except Exception as e:
            if running_flag.is_set():
                print(f"receive_audio error: {e}")

# order of execution:
# start_app() begins, initiates session to server
# THEN the core app can take place
# NOTE: start_app() not called here — UI.py drives the app now