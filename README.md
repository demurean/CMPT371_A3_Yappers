# Yappers

*2026-Spring* ||
*CMPT371 Networking* ||
*Simon Fraser University*

## **Team Members**

| Name           | Student ID | Email        |
|----------------|------------|--------------|
| Arielle Felicia  | 301597636 | afa85@sfu.ca |
| Tasha Gandevia | 301557333  | tga62@sfu.ca |


## Project Description

A real-time **push-to-talk (PTT) voice chat application** implemented in Python using UDP sockets. 

**Features:**
- Unique usernames for each client based on the NATO alphabet
- Two distinct channels to communicate on (one at a time)
- Status circles next to the username to indicate active talker and away (AFK)
- Push to talk

**Architecture:**
- Client–Server over TCP to communicate & keep track of client IPs over channels and usernames in the active session
- Peer-to-Peer over UDP for broadcasting voice and simulating walkie-talkies

**Additional Details:**
- Walkie-talkie style: only one user should speak at a time (not enforced, by convention)


## Quick-Start Guide

### Prerequisites

- Python version 3.13.1

### Install Python dependencies
PyAudio

```bash
# macOS
brew install portaudio
pip3 install pyaudio

# Windows
pip install pyaudio
```

### Run the app

1. Run the server on the host device
```bash
python serverUI.py
```
2. Open a new terminal for each client (on the same machine or different machines on the same network).

```bash
python clientUI.py
```
> *A popup will ask for the server IP. Press Enter to use `127.0.0.1` (if clients will be on the same machine), or type the server's local IP address (e.g. `192.168.1.42`) if connecting from another device.*

### Push to talk
- Press ```space``` to talk (or click the button)

### Stop
- Clients can close the application to disconnect. 
- Server app can click the ```End Server``` button to close the server, or close the application.
- `CTRL` + `C` from the terminal will also terminate the program.

## File Structure

```
CMPT371_A3_Yappers/
├── assets/
│    ├── wireframe.png # sketch of the GUI to reference   
│    ├── CLIENTlogo.ico # logo for client app
│    ├── logo.png
│    ├── SERVERlogo.ico # logo for server app
│    └── EvilLogo.png
│
├── server.py          # server -> registration, relay, timeout
├── serverUI.py        # server interface with Tkinter GUI.
├── client.py          # client -> audio capture/playback, communicates to server 
├── clientUI.py        # client interface with Tkinter GUI.
├── requirements.txt   # dependency list
├── notes.txt          # planning and meeting notes
├── A3_details.pdf     # assignment description and guideline
└── README.md          # this file
```


## Protocol Design

### Transport Layer

| Layer | Protocol | Port | Purpose |
|-------|----------|------|---------|
| Signalling | TCP | 5050 | Client ↔ Server: registration, channel management, push notifications |
| Audio | UDP | OS-assigned | Peer ↔ Peer: real-time audio streaming |


### TCP Message Format (Client → Server)

Messages are space-delimited. The server reads them with `recv(1024)`.

| Message | Format | Description |
|---------|--------|-------------|
| `LOBBY_ALL` | `LOBBY_ALL` | Request the full list of NATO usernames |
| `LOBBY_AVAIL` | `LOBBY_AVAIL` | Request only the currently available usernames |
| `REGISTER` | `REGISTER <username> <udp_port>` | Claim a username; includes the client's UDP port |
| `JOIN` | `JOIN <channel name>` | Join a channel (e.g. `JOIN Channel 1`) |
| `STATUS` | `STATUS <away\|active>` | Notify channel peers of AFK/active state change |
| `RETURN` | `RETURN` | Leave current channel, return to lobby |
| `GET_COUNT` | `GET_COUNT` | Request current member count per channel |


### TCP Message Format (Server → Client)

Messages from the server are either direct responses or `\n`-terminated push notifications.

| Message | Format | Description |
|---------|--------|-------------|
| `ALL_USERNAMES` | `ALL_USERNAMES <name> <name> ...` | Response to `LOBBY_ALL` |
| `AVAIL_USERNAMES` | `AVAIL_USERNAMES <name> <name> ...` | Response to `LOBBY_AVAIL` |
| `REGISTER_SUCCESS` | `REGISTER_SUCCESS` | Username successfully registered |
| `REGISTER_FAIL` | `REGISTER_FAIL` | Username already taken |
| `PEERS` | `PEERS <user>:<ip>:<port> ...` | Response to `JOIN`; list of all peers in channel |
| `CHANNEL_COUNT` | `CHANNEL_COUNT <ch>:<n>\|<ch>:<n>` | Response to `GET_COUNT` |
| `JOIN_NOTIFY` | `JOIN_NOTIFY <user>:<ip>:<port>\n` | Push: a new peer joined the channel |
| `LEAVE_NOTIFY` | `LEAVE_NOTIFY <username>\n` | Push: a peer left the channel |
| `STATUS_NOTIFY` | `STATUS_NOTIFY <username>:<away\|active>\n` | Push: a peer changed AFK state |
| `CHANNEL_COUNT_NOTIFY` | `CHANNEL_COUNT_NOTIFY <ch>:<n>\|<ch>:<n>\n` | Push: channel counts updated (sent to all clients) |

### UDP Audio Packet Format (Peer → Peer)

Audio is sent directly between clients with no server involvement.

```
[ 16 bytes: sender username (left-padded, null-filled) ][ N bytes: raw PCM audio ]
```

- **Encoding:** 16-bit signed PCM (`paInt16`, PyAudio's name for this format)
- **Sample rate:** 44,100 Hz
- **Channels:** Mono
- **Chunk size:** 1024 frames per packet
- Each client binds a UDP socket to port `0` (OS assigns a unique port), which is shared with the server during `REGISTER` so peers know where to send audio.
- _**Note**: Sample rate of 44,100 Hz was chosen because it's the "industry standard", not because the app specifically needed it. For VoIP, 16,000 would have been sufficient._ 

## Limitations & Known Issues
- `server.py` is not meant to be scaled up on. 
- This implementation(with no JSON) is expected to stay at its current size 
- There is no client menu so client app cannot start without server active: so server MUST BE STARTED FIRST
- _**NOTE**: An unknown maximum clients can connect to the server - Max tested was 6 on a single device, 3 on the network._

## Video Demo

#TODO


## References & Citations
- [Tutorial](https://www.pythontutorial.net/tkinter/) for creating Python apps
- [Tkinter framing](https://tkinterexamples.com/geometry/)
- [Stackoverflow](https://stackoverflow.com/questions/33137829/how-to-replace-the-icon-in-a-tkinter-app) for information on changing the logo 
- [ChatGPT](https://chatgpt.com/) to double-check edge cases in `server.py`
- Other references on server setup from resources provided in assignment description
- Course material