import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
import wave
import os

class DecodeTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.selected_file = None

        tk.Label(self, text="SSTV Decode (Audio → File)", font=("Arial", 14)).pack(pady=10)
        self.file_label = tk.Label(self, text="No audio selected", fg="gray")
        self.file_label.pack(pady=5)

        tk.Button(self, text="Select Audio", command=self.load_audio).pack(pady=5)
        tk.Button(self, text="Decode to File", command=self.decode_to_file).pack(pady=10)

    def load_audio(self):
        filetypes = [("Audio Files", "*.wav")]
        filename = filedialog.askopenfilename(title="Select Audio File", filetypes=filetypes)
        if filename:
            self.selected_file = filename
            self.file_label.config(text=os.path.basename(filename), fg="black")

    def decode_to_file(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select an audio file first!")
            return

        try:
            with wave.open(self.selected_file, "r") as wf:
                sample_rate = wf.getframerate()
                audio = np.frombuffer(wf.readframes(wf.getnframes()),
                                      dtype=np.int16).astype(np.float32) / 32767

            duration = 0.001
            chunk_size = int(sample_rate * duration)
            num_chunks = len(audio) // chunk_size

            low_freq = 1000
            high_freq = 2000

            bits = []
            for i in range(num_chunks):
                chunk = audio[i * chunk_size:(i + 1) * chunk_size]
                fft = np.fft.rfft(chunk)
                freqs = np.fft.rfftfreq(len(chunk), 1 / sample_rate)
                dom_freq = freqs[np.argmax(np.abs(fft))]

                bits.append("0" if abs(dom_freq - low_freq) < abs(dom_freq - high_freq) else "1")

            data = bytearray()
            for i in range(0, len(bits), 8):
                byte = bits[i:i + 8]
                if len(byte) == 8:
                    data.append(int("".join(byte), 2))

            output_file = os.path.splitext(self.selected_file)[0] + "_decoded.png"
            with open(output_file, "wb") as f:
                f.write(data)

            messagebox.showinfo("Success", f"File saved as:\n{output_file}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to decode audio: {e}")
