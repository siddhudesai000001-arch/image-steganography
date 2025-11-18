# main_gui.py

import tkinter as tk
from tkinter import ttk

from sstv_tab.encode_tab import EncodeTab
from sstv_tab.decode_tab import DecodeTab
from steg_tab.sender_tab import SenderTab
from steg_tab.receiver_tab import ReceiverTab

class SecureMessengerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Secure Messenger + SSTV")
        self.geometry("960x720")
        self.configure(bg="#eef2f7")  # clean soft light

        # ---------------- Styles ----------------
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TNotebook", background="#eef2f7")
        style.configure("TNotebook.Tab",
                        font=("Segoe UI", 11, "bold"),
                        padding=[20, 10],
                        background="#d7e3f4",
                        foreground="black")

        style.map("TNotebook.Tab",
                  background=[("selected", "#5a8dee")],
                  foreground=[("selected", "white")])

        style.configure("TFrame", background="#eef2f7")
        style.configure("TLabel", background="#eef2f7", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 11))

        # ---------------- Main Notebook ----------------
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=20, pady=20)

        # STEGANOGRAPHY
        steg = ttk.Notebook(notebook)
        steg.add(SenderTab(steg), text="Sender")
        steg.add(ReceiverTab(steg), text="Receiver")
        notebook.add(steg, text="Steganography")

        # SSTV
        sstv = ttk.Notebook(notebook)
        sstv.add(EncodeTab(sstv), text="Encode")
        sstv.add(DecodeTab(sstv), text="Decode")
        notebook.add(sstv, text="SSTV")

        # ---------------- Status Bar ----------------
        self.status = tk.Label(self, text="Ready",
                               bd=1, relief=tk.SUNKEN, anchor="w",
                               bg="#cdd8eb", font=("Segoe UI", 10))
        self.status.pack(fill="x", side="bottom")


if __name__ == "__main__":
    app = SecureMessengerApp()
    app.mainloop()
