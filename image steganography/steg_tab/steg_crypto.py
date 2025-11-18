# steg_tab/steg_crypto.py
# LSB steganography with JSON payload { "email": ..., "message": ... }

from PIL import Image
import math
import json

def _int_to_bits(value: int, length: int):
    return [(value >> i) & 1 for i in range(length-1, -1, -1)]

def _bits_to_int(bits):
    value = 0
    for b in bits:
        value = (value << 1) | (1 if b else 0)
    return value

def embed_secret_message(input_image_path: str, output_image_path: str, secret_message: str, recipient_email: str) -> None:
    """
    Embeds JSON payload {"email": recipient_email, "message": secret_message} into input image and saves as output_image_path.
    Raises ValueError if capacity insufficient.
    """
    if secret_message is None:
        raise ValueError("secret_message is None")
    if recipient_email is None:
        raise ValueError("recipient_email is None")

    payload = {"email": recipient_email, "message": secret_message}
    payload_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    img = Image.open(input_image_path)
    img = img.convert("RGBA")
    pixels = list(img.getdata())
    num_pixels = len(pixels)

    # header: 32-bit length (bytes)
    payload_length = len(payload_bytes)
    header_bits = _int_to_bits(payload_length, 32)

    message_bits = []
    for b in payload_bytes:
        message_bits.extend(_int_to_bits(b, 8))
    bits = header_bits + message_bits
    total_bits = len(bits)

    capacity = num_pixels * 3  # R,G,B LSBs
    if total_bits > capacity:
        raise ValueError(f"Image too small. Need {total_bits} bits but capacity is {capacity} bits.")

    new_pixels = []
    bit_idx = 0
    for (r, g, b, a) in pixels:
        r_new, g_new, b_new = r, g, b
        if bit_idx < total_bits:
            r_new = (r & ~1) | bits[bit_idx]; bit_idx += 1
        if bit_idx < total_bits:
            g_new = (g & ~1) | bits[bit_idx]; bit_idx += 1
        if bit_idx < total_bits:
            b_new = (b & ~1) | bits[bit_idx]; bit_idx += 1
        new_pixels.append((r_new, g_new, b_new, a))

    out_img = Image.new("RGBA", img.size)
    out_img.putdata(new_pixels)
    out_img.save(output_image_path, format="PNG")  # PNG to preserve LSBs

def decode_secret_payload(stego_image_path: str) -> dict:
    """
    Extract payload bytes and return parsed JSON dict {"email":..., "message":...}.
    This returns the payload without any OTP gating; caller should validate before revealing message.
    """
    img = Image.open(stego_image_path)
    img = img.convert("RGBA")
    pixels = list(img.getdata())

    bits = []
    for (r, g, b, a) in pixels:
        bits.append(r & 1)
        bits.append(g & 1)
        bits.append(b & 1)

    if len(bits) < 32:
        raise ValueError("Image too small or contains no payload header.")

    header_bits = bits[:32]
    payload_length = _bits_to_int(header_bits)
    required_bits = payload_length * 8
    if 32 + required_bits > len(bits):
        raise ValueError("Image does not contain the full payload (truncated).")

    payload_bits = bits[32:32 + required_bits]
    payload_bytes = bytearray()
    for i in range(0, len(payload_bits), 8):
        byte_bits = payload_bits[i:i+8]
        b = _bits_to_int(byte_bits)
        payload_bytes.append(b)
    try:
        payload_text = payload_bytes.decode("utf-8")
        payload = json.loads(payload_text)
        # expect payload to be dict with 'email' and 'message'
        return payload
    except Exception as e:
        raise ValueError(f"Failed to parse payload JSON: {e}")
