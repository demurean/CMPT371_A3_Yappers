import sys
import threading
import tkinter as tk

import server

# Colours
BG     = "#1e1e1e"
TOPBAR = "#141414"
FG     = "#ffffff"
DIM    = "#aaaaaa"
GREEN  = "#4CAF50"
RED    = "#f44336"
CARD   = "#2b2b2b"

# Can be changed later once we set theme
HF = ("Consolas", 24, "bold")       #Header
BF = ("Consolas", 12, "normal")     #Body
LF = ("Consolas", 9, "bold")

class ServerUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Yappers — Server")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._shutdown)
        self.root.iconbitmap("assets/SERVERlogo.ico")

        # Top bar
        top = tk.Frame(self.root, bg=TOPBAR, height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="Yappers Server", bg=TOPBAR, fg=FG,
                 font=HF).pack(side="left", padx=16, pady=12)

        tk.Button(top, text="End Server", command=self._shutdown,
                  bg=RED, fg=FG, relief="flat", font=BF,
                  padx=12, pady=4, cursor="hand2").pack(side="right", padx=16, pady=10)

        # Online count
        self._status_var = tk.StringVar(value="Online: 0")
        tk.Label(self.root, textvariable=self._status_var,
                 bg=BG, fg=DIM, font=BF).pack(anchor="w", padx=16, pady=(10, 4))

        # User list
        list_frame = tk.Frame(self.root, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Column headers
        header = tk.Frame(list_frame, bg=BG)
        header.pack(fill="x", pady=(0, 4))
        tk.Label(header, text="Username", bg=BG, fg=DIM,
                 font=BF, width=20, anchor="w").pack(side="left")
        tk.Label(header, text="Channel", bg=BG, fg=DIM,
                 font=BF, anchor="w").pack(side="left")

        tk.Frame(list_frame, bg="#444444", height=1).pack(fill="x", pady=(0, 6))

        self._list_inner = tk.Frame(list_frame, bg=BG)
        self._list_inner.pack(fill="both", expand=True)

        self._refresh()

    def _user_channel(self, uname: str) -> str:
        for ch_name, members in server.Channels.items():
            if uname in members:
                return ch_name
        return "(lobby)"

    def _refresh(self):
        """Rebuild the user list from live server state every 500 ms."""
        for w in self._list_inner.winfo_children():
            w.destroy()

        users = list(server.OnlineUsers.keys())
        self._status_var.set(f"Online: {len(users)}")

        for uname in users:
            row = tk.Frame(self._list_inner, bg=CARD, height=32)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            ch = self._user_channel(uname)
            color = DIM if ch == "(lobby)" else GREEN

            tk.Label(row, text=uname, bg=CARD, fg=FG,
                     font=BF, width=20, anchor="w").pack(side="left", padx=8)
            tk.Label(row, text=ch, bg=CARD, fg=color,
                     font=BF, anchor="w").pack(side="left")

        self.root.after(500, self._refresh)

    def _shutdown(self):
        """Stop accepting connections and exit."""
        print("Server shutting down...")
        try:
            if server.OnlineUsers.keys() != 0: # should do while? or nah
                server.TellClientsToShutDownToo()
            server.MySocket.close()
        except Exception:
            pass
        self.root.destroy()
        sys.exit(0)


# Entry point
threading.Thread(target=server.start_server, daemon=True).start()

root = tk.Tk()
ServerUI(root)
root.mainloop()