## README

*2026-Spring* ||
*CMPT371 Networking* ||
*Simon Fraser University*

> **Team Members**
> 
> | Name           | Student ID | Email        |
> |----------------|------------|--------------|
> | Arielle Felicia  | 301597636 | afa85@sfu.ca |
> | Tasha Gandevia | 301557333  | tga62@sfu.ca |

---

### Project Description

A real-time **push-to-talk (PTT) voice chat application** implemented in Python using UDP sockets. 

**Features:**
- Unique usernames for each client based on the NATO alphabet
- 2 Channels to communicate over on (one at a time)
- Status circles next to the username to indicate active talker and muted
- Push to talk.

**Architecture:**
- Client–Server over TCP to communicate & keep track of client IPs over channels and usernames in the active session
- Peer-to-Peer over UDP for broadcasting voice and simulating walkie-talkies

**Additional Details:**
- Only one user can speak at a time (as how walkie talkies are)

---

### Quick-Start Guide

#### Prerequisites

- Python version 3.13.1
- #TODO required installs


```bash
# macOS installs

# Windows installs
```

#### Install Python dependencies
PyAudio

```bash
pip3 install -r requirements.txt
```

#### Run the app

1. run the server once
```bash
python serverUI.py
```
2. open however much clients you want
Open a new terminal for each client (on the same machine or different machines on the same network).

```bash
python clientUI.py
```

#### Push to talk
Press ```space``` button to talk.

#### Stop
Clients can close the application to disconnect.
Server app can click the ```End Server``` button to close the server, or close the application.

---

### File Structure

```
CMPT371_A3_Yappers/
├── assets/
│    ├── wireframe.png # sketch of the GUI to reference   
│    └── 
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

---

### Protocol Design

#TODO

---

### Limitations & Known Issues
server.py is not meant to be scaled up on. This implementation(with no JSON) is expected to stay at its current size

---

### Video Demo

#TODO

---

### References & Citations
- Double checked for edge cases in server.py with ChatGPT
- Tkinter tutorial to make the python app https://www.pythontutorial.net/tkinter/
- other references on server setting up from resources provided in assignment description
- ChatGPT for fixing the break-up of server.py to clientUI.py and client.py (most notably when the channels dont show up)