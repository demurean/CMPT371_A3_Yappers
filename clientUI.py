import socket
import threading
import tkinter as tk
from tkinter import ttk

import client

# Colours
BG     = "#2b2b2b"
TOPBAR = "#1e1e1e"
CARD   = "#3c3c3c"
FG     = "#ffffff"
DIM    = "#aaaaaa"
BTN    = "#444444"
GREEN  = "#4CAF50"
YELLOW = "#FFC107"
RED    = "#f44336"
ACCENT = "#aaaaff"

AVAILABLE_USERNAMES = []
CHANNEL_INFO = {"Channel 1": 0, "Channel 2": 0}


# Can be changed later once we set theme
HF = ("Consolas", 20, "bold")       #Header
BF = ("Consolas", 12, "normal")     #Body
LF = ("Consolas", 8, "bold")        #Label

class YappersApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Yappers")
        self.root.geometry("750x500")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # ── App state ─────────────────────────────────────────────────────────
        self.username: str | None        = None
        self.current_channel: str | None = None
        self.is_away    = False
        self.is_talking = threading.Event()   # set = currently talking

        # {username: status}  status ∈ {"idle","talking","muted"}
        self.channel_users: dict[str, str]    = {}
        # {username: canvas}  canvas holding the coloured dot
        self.user_circles: dict[str, tk.Canvas] = {}

        # ── Server socket (TCP) ───────────────────────────────────────────────
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((client.SERVER_HOST, client.SERVER_PORT))

        # {peer_username: (ip, port)}
        # TODO: populate from server JOIN response ("PEERS ip:port …")
        self.peers: dict[str, tuple[str, int]] = {}

        # ── UDP + PyAudio ────────────────────────────────────────────────────
        self.udp_sock        = client.setup_udp()
        self.pa              = client.pyaudio.PyAudio() if client.PYAUDIO_AVAILABLE else None
        self.record_stream   = None
        self.playback_stream = None

        # ── Receiver thread ───────────────────────────────────────────────────
        self.running = threading.Event()
        self.running.set()
        self._open_playback()
        threading.Thread(
            target=client.receive_audio_loop,
            args=(self.udp_sock, self.playback_stream,
                  self.running, self._on_audio_from),
            daemon=True,
        ).start()

        # ── Keyboard PTT (spacebar) ───────────────────────────────────────────
        self.root.bind("<KeyPress-space>",   self.start_talking)
        self.root.bind("<KeyRelease-space>", self.stop_talking)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._frame: tk.Frame | None = None
        self.show_username_lobby()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _clear(self):
        if self._frame:
            self._frame.destroy()
            self._frame = None

    @staticmethod
    def _color(status: str) -> str:
        return {
            "talking": GREEN,
            "away":    RED,
        }.get(status, YELLOW)

    def _open_playback(self):
        if not (client.PYAUDIO_AVAILABLE and self.pa):
            return
        try:
            self.playback_stream = self.pa.open(
                format=client.FORMAT, channels=client.CHANNELS,
                rate=client.RATE, output=True,
                frames_per_buffer=client.CHUNK,
            )
        except Exception as e:
            print(f"Playback open failed: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # SCREEN 1 — Username lobby
    # ══════════════════════════════════════════════════════════════════════════

    def show_username_lobby(self):
        self._clear()
        frame = tk.Frame(self.root, bg=BG)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        self._frame = frame

        tk.Label(frame, text="Please select a username",
                 bg=BG, fg=FG, font=HF).pack(pady=(0, 16))

        row = tk.Frame(frame, bg=BG)
        row.pack(pady=(0, 16))

        self._uvar = tk.StringVar()
        # values come from server LOBBY response
        AVAILABLE_USERNAMES = client.GetAvailableUsernames(self.server_socket)
        self._username_cb = ttk.Combobox(row, textvariable=self._uvar,
                                         values=AVAILABLE_USERNAMES,
                                         state="readonly", width=28)
        self._username_cb.pack(side="left", padx=(0, 4))

        tk.Button(row, text="✓", command=self._confirm_username,
                  bg=BTN, fg=FG, relief="flat", padx=8, pady=4).pack(side="left")

        self._username_error = tk.Label(frame, text="",
                                        bg=BG, fg=RED, font=BF)
        self._username_error.pack(pady=(8, 0))

        # TODO Tutorial / Info
        tk.Label(frame, text="link to dif page for tutorial",
                 bg=BG, fg=DIM, font=LF,
                 cursor="hand2").pack()

    def _confirm_username(self):
        name = self._uvar.get().strip()
        if not name:
            return

        # parsing for REGISTER_SUCCESS
        resp = client.RegisterUsername(self.server_socket, name)
        if resp != "REGISTER_SUCCESS":
            self._username_error.config(text=f'"{name}" is already taken. Please choose another.')
            fresh = client.GetAvailableUsernames(self.server_socket)
            self._username_cb.config(values=fresh)
            self._uvar.set("")
            return

        self.username = name
        # if name in AVAILABLE_USERNAMES:
        #     AVAILABLE_USERNAMES.remove(name)   # mock: claim name locally
        # NOTE: ^^ should be handled server-side already

        self.show_channel_lobby()

    # ══════════════════════════════════════════════════════════════════════════
    # SCREEN 2 — Channel lobby
    # ══════════════════════════════════════════════════════════════════════════

    def show_channel_lobby(self):
        self._clear()
        frame = tk.Frame(self.root, bg=BG)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        self._frame = frame

        tk.Label(frame,
                 text=f"Welcome {self.username}!\nPlease select a channel to connect to.",
                 bg=BG, fg=FG, font=HF, justify="center").pack(pady=(0, 28))
        
        # updating CHANNEL_INFO as well
        CHANNEL_INFO = client.GetUserCountperChannel(self.server_socket)
        for ch_name, count in CHANNEL_INFO.items():
            self._channel_card(frame, ch_name, count)

    def _channel_card(self, parent: tk.Frame, ch_name: str, count: int):
        card = tk.Frame(parent, bg="white", width=320, height=80,
                        relief="solid", bd=1, cursor="hand2")
        card.pack(pady=8)
        card.pack_propagate(False)

        inner = tk.Frame(card, bg="white")
        inner.place(relx=0.08, rely=0.5, anchor="w")
        tk.Label(inner, text=ch_name, bg="white", fg="black",
                 font=BF).pack(anchor="w")
        tk.Label(inner, text=f"{count} Active users", bg="white", fg="#555",
                 font=BF).pack(anchor="w")

        for w in (card, inner, *inner.winfo_children()):
            w.bind("<Button-1>", lambda _e, ch=ch_name: self._join_channel(ch))

    def _join_channel(self, ch_name: str):
        # TODO: call client.channel_lobby(self.server_socket) — adapted for GUI:
        # self.server_socket.sendall(f"JOIN {ch_name}".encode())
        # resp = self.server_socket.recv(1024).decode().strip()
        # parts = resp.split()
        # if parts[0] == "PEERS":
        #     for peer_str in parts[1:]:          # "ip:port"
        #         ip, port = peer_str.rsplit(":", 1)
        #         # NOTE: server needs to also send peer username alongside ip:port
        #         # self.peers[peer_username] = (ip, int(port))
        peers = client.JoinChannel(self.server_socket, ch_name, self.username)
        self.peers = peers
        print("peers from __join_channel ", peers)
        self.current_channel = ch_name
        self.channel_users = {self.username: "idle"}

        for x in peers: # peers[username] = ip, port
            self.channel_users[x] = "idle"
            print(x)

        self.show_channel()

        # start listener for push notifications (JOIN_NOTIFY / LEAVE_NOTIFY)
        self._listen_flag = threading.Event()
        self._listen_flag.set()
        threading.Thread(target=self._server_listener, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # SCREEN 3 — In channel
    # ══════════════════════════════════════════════════════════════════════════

    def show_channel(self):
        self._clear()
        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)
        self._frame = frame

        # ── Top bar ───────────────────────────────────────────────────────────
        top = tk.Frame(frame, bg=TOPBAR)
        top.pack(fill="x")

        tk.Label(top, text=f"USERNAME: {self.username}",
                 bg=TOPBAR, fg=FG, font=LF).pack(side="left", padx=16, pady=10)

        back = tk.Label(top, text=f"Return to Lobby",
                        bg=TOPBAR, fg=ACCENT,
                        font=BF, cursor="hand2")
        back.pack(side="right", padx=16, pady=10)
        back.bind("<Button-1>", self._return_to_lobby)

        # ── User cards ────────────────────────────────────────────────────────
        self._cards = tk.Frame(frame, bg=BG)
        self._cards.pack(fill="both", expand=True, padx=28, pady=20)
        self._rebuild_cards()

        # ── Bottom bar ────────────────────────────────────────────────────────
        bot = tk.Frame(frame, bg=TOPBAR, height=62)
        bot.pack(fill="x", side="bottom")
        bot.pack_propagate(False)

        # Push-to-talk
        ptt = tk.Frame(bot, bg=TOPBAR)
        ptt.pack(side="left", padx=28, pady=12)

        self._ptt_dot = tk.Canvas(ptt, width=20, height=20, bg=TOPBAR, highlightthickness=0)
        self._ptt_dot.create_oval(2, 2, 18, 18, fill=GREEN, tags="dot")
        self._ptt_dot.pack(side="left", padx=(0, 6))

        self._ptt_btn = tk.Button(ptt, text="Push to talk",
                                  bg=BTN, fg=FG, relief="flat", font=LF, padx=12, pady=4)
        self._ptt_btn.pack(side="left")
        self._ptt_btn.bind("<ButtonPress-1>",   self.start_talking)
        self._ptt_btn.bind("<ButtonRelease-1>", self.stop_talking)

        tk.Label(ptt, text="OR press spacebar",
                 bg=TOPBAR, fg=DIM, font=LF).pack(side="left", padx=8)

        self._ptt_msg = tk.Label(ptt, text="", bg=TOPBAR, fg=RED, font=LF)
        self._ptt_msg.pack(side="left", padx=8)

        # Away toggle
        mut = tk.Frame(bot, bg=TOPBAR)
        mut.pack(side="left", padx=8, pady=12)

        self._away_dot = tk.Canvas(mut, width=20, height=20, bg=TOPBAR, highlightthickness=0)
        self._away_dot.create_oval(2, 2, 18, 18, fill=YELLOW, tags="dot")
        self._away_dot.pack(side="left", padx=(0, 6))

        self._away_btn = tk.Button(mut, text="Set Away",
                                   bg=BTN, fg=FG, relief="flat", font=LF,
                                   padx=12, pady=4, command=self.toggle_away)
        self._away_btn.pack(side="left")

    # ── Card grid ─────────────────────────────────────────────────────────────

    def _rebuild_cards(self):
        for w in self._cards.winfo_children():
            w.destroy()
        self.user_circles.clear()

        for idx, (uname, status) in enumerate(self.channel_users.items()):
            r, c = divmod(idx, 3)
            card = tk.Frame(self._cards, bg=CARD, width=170, height=58)
            card.grid(row=r, column=c, padx=10, pady=10, sticky="nw")
            card.grid_propagate(False)

            inner = tk.Frame(card, bg=CARD)
            inner.place(relx=0.08, rely=0.5, anchor="w")
            tk.Label(inner, text=uname, bg=CARD, fg=FG,
                     font=BF).pack(side="left", padx=(0, 8))

            dot = tk.Canvas(inner, width=20, height=20, bg=CARD, highlightthickness=0)
            dot.create_oval(2, 2, 18, 18, fill=self._color(status), tags="dot")
            dot.pack(side="left")
            self.user_circles[uname] = dot

    def _set_status(self, uname: str, status: str):
        self.channel_users[uname] = status
        if uname in self.user_circles:
            self.user_circles[uname].itemconfig("dot", fill=self._color(status))

    # ── Server push listener ──────────────────────────────────────────────────

    def _server_listener(self):
        self.server_socket.settimeout(1.0)
        buf = ""
        while self._listen_flag.is_set():
            try:
                data = self.server_socket.recv(1024).decode()
                if not data:
                    break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    self._handle_push(line.strip())
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_push(self, msg):
        parts = msg.split()
        if not parts:
            return
        if parts[0] == "JOIN_NOTIFY" and len(parts) > 1:
            username, ip, port = parts[1].rsplit(":", 2)
            self.root.after(0, self._add_peer, username, ip, int(port))
        elif parts[0] == "LEAVE_NOTIFY" and len(parts) > 1:
            self.root.after(0, self._remove_peer, parts[1])
        elif parts[0] == "STATUS_NOTIFY" and len(parts) > 1:
            uname, status = parts[1].rsplit(":", 1)
            self.root.after(0, self._set_status, uname, status)

    def _add_peer(self, username, ip, port):
        if not self.current_channel or username in self.channel_users:
            return
        self.channel_users[username] = "idle"
        self.peers[username] = (ip, port)
        self._rebuild_cards()

    def _remove_peer(self, username):
        if not self.current_channel:
            return
        self.channel_users.pop(username, None)
        self.peers.pop(username, None)
        self._rebuild_cards()

    # ── Navigation ────────────────────────────────────────────────────────────

    def _return_to_lobby(self, _event=None):
        self.stop_talking()
        self.is_away = False
        if hasattr(self, '_listen_flag'):
            self._listen_flag.clear()
        try:
            self.server_socket.sendall(b"RETURN")
        except Exception:
            pass
        self.current_channel = None
        self.channel_users.clear()
        self.show_channel_lobby()

    # ══════════════════════════════════════════════════════════════════════════
    # Push-to-Talk
    # ══════════════════════════════════════════════════════════════════════════

    def start_talking(self, _event=None):
        if self.is_away:
            if hasattr(self, '_ptt_msg'):
                self._ptt_msg.config(text="Clear Away status to talk")
                self.root.after(2500, lambda: self._ptt_msg.config(text="") if self._ptt_msg.winfo_exists() else None)
            return
        if self.is_talking.is_set() or self.current_channel is None:
            return
        if not (client.PYAUDIO_AVAILABLE and self.pa):
            return

        try:
            self.record_stream = self.pa.open(
                format=client.FORMAT, channels=client.CHANNELS,
                rate=client.RATE, input=True,
                frames_per_buffer=client.CHUNK,
            )
        except Exception as e:
            print(f"Mic open failed: {e}")
            return

        self.is_talking.set()
        self._set_status(self.username, "talking")

        print("Peers from start_talking", self.peers)

        threading.Thread(
            target=client.send_audio_loop,
            args=(self.record_stream, self.udp_sock,
                  self.peers, self.username, self.is_talking),
            daemon=True,
        ).start()

    def stop_talking(self, _event=None):
        if not self.is_talking.is_set():
            return
        self.is_talking.clear()
        self._set_status(self.username, "idle")

        if self.record_stream:
            try:
                self.record_stream.stop_stream()
                self.record_stream.close()
            except Exception:
                pass
            self.record_stream = None

    def toggle_away(self):
        self.is_away = not self.is_away
        if self.is_away:
            self._away_btn.config(text="Clear Away")
            self._away_dot.itemconfig("dot", fill=RED)
            self.stop_talking()
            self._set_status(self.username, "away")
            try:
                self.server_socket.sendall(b"STATUS away")
            except Exception:
                pass
        else:
            self._away_btn.config(text="Set Away")
            self._away_dot.itemconfig("dot", fill=YELLOW)
            self._set_status(self.username, "idle")
            try:
                self.server_socket.sendall(b"STATUS active")
            except Exception:
                pass

    # ── Audio receive callback ────────────────────────────────────────────────

    def _on_audio_from(self, sender: str):
        """Called by receive_audio_loop thread when a packet arrives."""
        if sender not in self.channel_users:
            return
        self.root.after(0, self._set_status, sender, "talking")
        self.root.after(350, self._maybe_reset, sender)

    def _maybe_reset(self, uname: str):
        if self.channel_users.get(uname) == "talking":
            self._set_status(uname, "idle")

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def _on_close(self):
        self.running.clear()
        self.is_talking.clear()
        if hasattr(self, '_listen_flag'):
            self._listen_flag.clear()

        try:
            self.server_socket.sendall(b"RETURN")
            self.server_socket.close()
        except Exception:
            pass

        for stream in (self.record_stream, self.playback_stream):
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
        if self.pa:
            self.pa.terminate()
        try:
            self.udp_sock.close()
        except Exception:
            pass
        self.root.destroy()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    YappersApp(root)
    root.mainloop()
