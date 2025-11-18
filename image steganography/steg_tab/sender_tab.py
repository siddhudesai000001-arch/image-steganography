# steg_tab/sender_tab.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from .steg_crypto import embed_secret_message

class SenderTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.image_path = tk.StringVar()
        self.secret_msg = tk.StringVar()
        self.recipient_email = tk.StringVar()

        tk.Label(self, text="Sender - Embed Secret Message", font=("Arial", 16, "bold")).pack(pady=10)

        frame_img = ttk.Frame(self)
        frame_img.pack(pady=10, fill="x", padx=20)
        ttk.Label(frame_img, text="Cover Image:").pack(side="left")
        ttk.Entry(frame_img, textvariable=self.image_path, width=50).pack(side="left", padx=5)
        ttk.Button(frame_img, text="Browse", command=self.browse_image).pack(side="left")

        frame_msg = ttk.Frame(self)
        frame_msg.pack(pady=10, fill="x", padx=20)
        ttk.Label(frame_msg, text="Secret Message:").pack(side="left")
        ttk.Entry(frame_msg, textvariable=self.secret_msg, width=50).pack(side="left", padx=5)

        frame_email = ttk.Frame(self)
        frame_email.pack(pady=10, fill="x", padx=20)
        ttk.Label(frame_email, text="Recipient Email:").pack(side="left")
        ttk.Entry(frame_email, textvariable=self.recipient_email, width=40).pack(side="left", padx=5)

        ttk.Button(self, text="Embed & Save", command=self.embed_and_save).pack(pady=20)

    def browse_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")]
        )
        if file_path:
            self.image_path.set(file_path)

    def embed_and_save(self):
        if not self.image_path.get() or not self.secret_msg.get() or not self.recipient_email.get():
            messagebox.showerror("Error", "Please select an image, enter a message, and provide recipient email")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
            title="Save Stego-Image As"
        )
        if save_path:
            try:
                embed_secret_message(self.image_path.get(), save_path, self.secret_msg.get(), self.recipient_email.get().strip())
                messagebox.showinfo("Success", f"Stego-image saved at:\n{save_path}")
                try:
                    os.startfile(os.path.dirname(save_path))
                except Exception:
                    pass
            except Exception as e:
                messagebox.showerror("Error", f"Failed to embed message:\n{str(e)}")
