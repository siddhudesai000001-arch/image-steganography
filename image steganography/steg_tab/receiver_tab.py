# steg_tab/receiver_tab.py
import os
import threading
import random
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from email.message import EmailMessage
import smtplib

from .steg_crypto import decode_secret_payload

# OTP settings
OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 300  # 5 minutes
MAX_OTP_ATTEMPTS = 3

# SMTP config (hardcoded per your request)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USERNAME = "gdfg33379@gmail.com"
SMTP_PASSWORD = "indeybktmqywpmfa"  # app password (spaces removed)

def generate_otp(length=OTP_LENGTH):
    return f"{random.randint(0, 10**length - 1):0{length}d}"

def send_email_smtp(to_email: str, subject: str, body: str):
    if not (SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD):
        raise RuntimeError("SMTP configuration missing.")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USERNAME
    msg["To"] = to_email
    msg.set_content(body)
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

class ReceiverTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.image_path = tk.StringVar()

        # payload will hold dict {'email':..., 'message':...} after reading file
        self._payload = None

        # OTP state
        self._current_otp = None
        self._otp_expiry = 0
        self._is_sending = False

        tk.Label(self, text="Receiver - Decode Hidden Message", font=("Arial", 16, "bold")).pack(pady=8)

        frame_img = ttk.Frame(self)
        frame_img.pack(pady=8, fill="x", padx=20)
        ttk.Label(frame_img, text="Stego Image:").pack(side="left")
        ttk.Entry(frame_img, textvariable=self.image_path, width=50).pack(side="left", padx=6)
        ttk.Button(frame_img, text="Browse", command=self.browse_image).pack(side="left")

        # show extracted recipient email (read-only) once image chosen
        self.recipient_email_var = tk.StringVar(value="(no recipient email detected yet)")
        ttk.Label(self, text="Recipient Email:").pack(pady=(10,0))
        ttk.Label(self, textvariable=self.recipient_email_var, foreground="blue").pack()

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var).pack(pady=(6,4))

        self.otp_button = ttk.Button(self, text="Request OTP & Decode", command=self.request_otp_flow)
        self.otp_button.pack(pady=10)

        self.msg_display = tk.Text(self, height=8, width=78, wrap="word", font=("Arial", 12), state="disabled")
        self.msg_display.pack(pady=6, padx=20)
        ttk.Button(self, text="Copy Message", command=self.copy_message).pack(pady=6)

    def browse_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Stego Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if file_path:
            self.image_path.set(file_path)
            # immediate read payload (email+message) but DO NOT display message
            try:
                payload = decode_secret_payload(file_path)
                if not isinstance(payload, dict) or "email" not in payload or "message" not in payload:
                    raise ValueError("Payload missing expected fields")
                self._payload = payload
                self.recipient_email_var.set(payload.get("email", "(no email)"))
                self.status_var.set("Payload read: recipient email detected")
            except Exception as e:
                self._payload = None
                self.recipient_email_var.set("(no recipient email detected)")
                self.status_var.set("No valid payload detected")
                messagebox.showwarning("Payload read warning", f"Could not read payload from image:\n{e}")

    # OTP flow
    def request_otp_flow(self):
        if not self.image_path.get():
            messagebox.showerror("Error", "Please select a stego-image first.")
            return
        if not self._payload:
            messagebox.showerror("Error", "No embedded payload found in the image.")
            return
        to_email = self._payload.get("email")
        if not to_email:
            messagebox.showerror("Error", "Payload does not contain recipient email.")
            return

        # generate and send OTP
        self._current_otp = generate_otp()
        self._otp_expiry = time.time() + OTP_EXPIRY_SECONDS
        self._set_sending_state(True)
        self.status_var.set("Sending OTP...")

        t = threading.Thread(target=self._send_otp_background, args=(to_email, self._current_otp), daemon=True)
        t.start()

    def _set_sending_state(self, sending: bool):
        self._is_sending = sending
        if sending:
            self.otp_button.state(["disabled"])
        else:
            self.otp_button.state(["!disabled"])

    def _send_otp_background(self, to_email, otp):
        subject = "Your verification code"
        body = f"Your verification code is: {otp}\nThis code will expire in {OTP_EXPIRY_SECONDS//60} minutes."
        error = None
        try:
            send_email_smtp(to_email, subject, body)
        except Exception as e:
            error = str(e)

        def on_done():
            self._set_sending_state(False)
            if error:
                self.status_var.set("Failed to send OTP")
                messagebox.showerror("OTP Send Error", f"Failed to send OTP email:\n{error}")
            else:
                self.status_var.set("OTP sent — waiting for input")
                messagebox.showinfo("OTP Sent", f"An OTP has been sent to {to_email}. It will expire in {OTP_EXPIRY_SECONDS//60} minutes.")
                self._prompt_for_otp_and_verify()
        self.after(50, on_done)

    def _prompt_for_otp_and_verify(self):
        attempts = 0
        while attempts < MAX_OTP_ATTEMPTS:
            attempts += 1
            otp_input = simpledialog.askstring("Enter OTP", f"Enter the {OTP_LENGTH}-digit OTP sent to your email (Attempt {attempts}/{MAX_OTP_ATTEMPTS}):", parent=self)
            if otp_input is None:
                self.status_var.set("OTP verification cancelled")
                return
            ok, reason = self._verify_otp(otp_input.strip())
            if ok:
                self.status_var.set("OTP verified — decoding...")
                self._reveal_message()
                return
            else:
                messagebox.showwarning("Invalid OTP", reason)
                self.status_var.set("Invalid OTP")
                if attempts >= MAX_OTP_ATTEMPTS:
                    messagebox.showerror("Failed", "Maximum OTP attempts reached. Aborting.")
                    self.status_var.set("OTP verification failed")
                    return

    def _verify_otp(self, otp_input: str):
        if self._current_otp is None:
            return False, "No OTP requested. Please request OTP first."
        if time.time() > self._otp_expiry:
            return False, "OTP expired. Please request a new OTP."
        if not otp_input.isdigit() or len(otp_input) != OTP_LENGTH:
            return False, f"OTP must be {OTP_LENGTH} digits."
        if otp_input != self._current_otp:
            return False, "OTP incorrect."
        self._current_otp = None
        self._otp_expiry = 0
        return True, ""

    def _reveal_message(self):
        if not self._payload:
            messagebox.showerror("Error", "No payload available.")
            return
        hidden_message = self._payload.get("message", "")
        self.msg_display.config(state="normal")
        self.msg_display.delete("1.0", tk.END)
        self.msg_display.insert(tk.END, hidden_message)
        self.msg_display.config(state="disabled")
        self.status_var.set("Decoded — message displayed")
        messagebox.showinfo("Done", "Hidden message revealed.")

    def copy_message(self):
        text = self.msg_display.get("1.0", tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Message copied to clipboard!")
        else:
            messagebox.showwarning("Warning", "No message to copy!")
