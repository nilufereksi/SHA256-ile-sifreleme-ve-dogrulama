# client_slave.py (düzeltilmiş)
import os
import sys
import socket
import struct
from typing import List, Tuple
import hashlib

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes

from audio_tools import record_audio, audio_to_blocks
from audio_hash import hash_blocks

HOST = "127.0.0.1"
PORT = 5000

def pack_hashes(hash_list):
    out = struct.pack(">I", len(hash_list))
    for h in hash_list:
        out += h
    return out

def recv_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Bağlantı kesildi.")
        data += chunk
    return data

def recv_packet(sock):
    hdr = recv_exact(sock, 4)
    length = struct.unpack(">I", hdr)[0]
    return recv_exact(sock, length)

def send_packet(sock, payload: bytes):
    sock.sendall(struct.pack(">I", len(payload)) + payload)

def aes_gcm_encrypt(p1: bytes, plaintext: bytes):
    nonce = get_random_bytes(12)
    cipher = AES.new(p1, AES.MODE_GCM, nonce=nonce)
    ct, tag = cipher.encrypt_and_digest(plaintext)
    return nonce, tag, ct

def build_payload(msg_type: int, plain_bytes: bytes):
    return msg_type, plain_bytes

def get_hashes_from_fresh_record(seconds=3, wav_name="kayit.wav") -> List[bytes]:
    record_audio(wav_name, duration=seconds)
    blocks = audio_to_blocks(wav_name)
    hashes = hash_blocks(blocks)
    return hashes

# --- Haber modülü (düzeltilmiş) ---
def get_news_hashes_from_file(file_path: str) -> List[bytes]:
    import hashlib, os

    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    hashes = []
    try:
        with open(file_path, "rb") as f:
            content = f.read()

        for i in range(0, len(content), 8):
            block = content[i:i+8]
            if len(block) < 8:
                continue
            h = hashlib.sha256(block).digest()
            hashes.append(h)

        if hashes:
            print(f"[DEBUG] {file_path}: {len(hashes)} hash üretildi.")
            print(f"İlk hash: {hashes[0].hex()[:16]}...")
        else:
            print(f"[DEBUG] {file_path}: hiç hash üretilemedi.")

        return hashes

    except Exception as e:
        print(f"[ERROR] {file_path} hash alınırken hata: {e}")
        return []



def get_news_hashes_from_files(file_list: List[str]) -> List[bytes]:
    all_hashes = []
    for file in file_list:
        all_hashes.extend(get_news_hashes_from_file(file))
    return all_hashes

# ----- Yeni: iki haber dosyasını bir payload'ta paketleme -----
def build_two_file_payload(list_a: List[bytes], list_b: List[bytes]) -> bytes:
    return pack_hashes(list_a) + pack_hashes(list_b)

# ----------------------------------------------------------------
# Client-side run function (GUI burayı çağıracak)
# ----------------------------------------------------------------
def run_client(mode: str, args) -> Tuple[bool, str]:
    """
    mode: 'enroll'|'verify'|'news-enroll'|'news-verify'|'news-compare'
    args:
      - enroll/verify: seconds (int) optionally
      - news-enroll/news-verify: list of file paths
      - news-compare: tuple/list of two file paths (fileA, fileB)
    Returns (ok:bool, message:str)
    """
    if mode in ("enroll", "verify"):
        seconds = int(args) if args is not None else 3
        hashes = get_hashes_from_fresh_record(seconds=seconds)
        msg_type = 1 if mode == "enroll" else 2
        plaintext = pack_hashes(hashes)

    elif mode in ("news-enroll", "news-verify"):
        file_list = list(args) if args is not None else []
        if not file_list:
            return False, "No news files provided"
        hashes = get_news_hashes_from_files(file_list)
        msg_type = 3 if mode == "news-enroll" else 4
        plaintext = pack_hashes(hashes)

    elif mode == "news-compare":
        if not args or len(args) < 2:
            return False, "Need two files for news-compare"
        fileA, fileB = args[0], args[1]
        list_a = get_news_hashes_from_file(fileA)
        list_b = get_news_hashes_from_file(fileB)
        msg_type = 5
        plaintext = build_two_file_payload(list_a, list_b)

    else:
        return False, "Invalid mode"

    # --- network ---
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))

            server_pub_pem = recv_packet(sock)
            server_pub = RSA.import_key(server_pub_pem)

            p1 = get_random_bytes(32)
            rsa_cipher = PKCS1_OAEP.new(server_pub)
            enc_p1 = rsa_cipher.encrypt(p1)
            send_packet(sock, enc_p1)

            nonce, tag, ct = aes_gcm_encrypt(p1, plaintext)
            frame = bytes([msg_type]) + nonce + tag + struct.pack(">I", len(ct)) + ct
            send_packet(sock, frame)

            resp = recv_packet(sock)
            if not resp:
                return False, "Empty response"

            code = resp[0]
            text = resp[1:].decode(errors="ignore") if len(resp) > 1 else ""
            ok = code == 1
            return ok, text

    except Exception as e:
        return False, f"Network/error: {e}"


# ----------------------------------------------------------------
# CLI compatibility (eski kullanım korunur)
# ----------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Kullanım: python client_slave.py enroll|verify|news-enroll|news-verify|news-compare [dosyalar/süre]")
        return

    mode = sys.argv[1]
    if mode in ("enroll", "verify"):
        seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        ok, msg = run_client(mode, seconds)
        print((" OK" if ok else " FAIL"), msg)

    elif mode in ("news-enroll", "news-verify"):
        file_list = sys.argv[2:]
        ok, msg = run_client(mode, file_list)
        print((" OK" if ok else " FAIL"), msg)

    elif mode == "news-compare":
        if len(sys.argv) < 4:
            print("news-compare usage: client_slave.py news-compare fileA fileB")
            return
        fileA = sys.argv[2]
        fileB = sys.argv[3]
        ok, msg = run_client("news-compare", (fileA, fileB))
        print((" OK" if ok else " FAIL"), msg)

    else:
        print("Geçersiz mod.")


if __name__ == "__main__":
    main()


