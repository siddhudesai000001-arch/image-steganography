import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
import wave
import os

class EncodeTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.selected_file = None

        tk.Label(self, text="SSTV Encode (Image → Audio)", font=("Arial", 14)).pack(pady=10)
        self.file_label = tk.Label(self, text="No image selected", fg="gray")
        self.file_label.pack(pady=5)

        tk.Button(self, text="Select Image", command=self.load_image).pack(pady=5)
        tk.Button(self, text="Convert to Audio", command=self.convert_to_audio).pack(pady=10)

    def load_image(self):
        filetypes = [("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select Image", filetypes=filetypes)
        if filename:
            self.selected_file = filename
            self.file_label.config(text=os.path.basename(filename), fg="black")

    def convert_to_audio(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select an image first!")
            return
        try:
            with open(self.selected_file, "rb") as f:
                data = f.read()

            bits = ''.join(f"{byte:08b}" for byte in data)

            sample_rate = 16000
            duration = 0.001
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            low_freq = 1000
            high_freq = 2000

            audio = []
            for bit in bits:
                freq = high_freq if bit == "1" else low_freq
                audio.extend(np.sin(2*np.pi*freq*t))

            audio = np.array(audio, dtype=np.float32)
            output_file = os.path.splitext(self.selected_file)[0] + "_sstv.wav"

            with wave.open(output_file, "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes((audio * 32767).astype(np.int16).tobytes())

            messagebox.showinfo("Success", f"Audio saved as:\n{output_file}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to encode image: {e}")
