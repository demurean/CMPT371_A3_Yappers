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

```bash
# requirements file attached
pip3 install -r requirements.txt
```

#### Run the server

```bash
# to start the server
python server.py
```

#### Connect clients

Open a new terminal for each client (on the same machine or different machines on the same network).

```bash
python client.py
```

**Instructions to Connect:**
- #TODO

#### Push to talk

- #TODO

#### Stop

- #TODO

---

### File Structure

```
CMPT371_A3_Yappers/
├── server.py          # server -> registration, relay, timeout
├── client.py          # client -> audio capture/playback, Tkinter GUI
├── requirements.txt   # dependency list
├── notes.txt          # planning and meeting notes
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