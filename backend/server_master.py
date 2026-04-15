# server_master.py (duzeltilmis — tum dosya)
import os
import socket
import struct
import hashlib

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES

from rsa_keys import anahtar_uret, yukle_kamu, yukle_ozel

# --- KALICI DEPOLAMA ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

STORE_DIR = os.path.join(PROJECT_DIR, "server_data")
STORE_FILE = os.path.join(STORE_DIR, "enrolled_hashes.bin")

HABER_DIR = os.path.join(PROJECT_DIR, "haberler")
HABER_STORE_FILE = os.path.join(HABER_DIR, "enrolled_news_hashes.bin")

# --- NETWORK / ESIKLER ---
HOST = "127.0.0.1"
PORT = 5000
THRESHOLD = 0.6      # ses icin eslesme esigi
NEWS_THRESHOLD = 0.6 # kullanilmiyor ama birakildi

def ensure_keys():
    keys_dir = os.path.join(PROJECT_DIR, "anahtarlar")
    os.makedirs(keys_dir, exist_ok=True)
    priv = os.path.join(keys_dir, "bob_private.pem")
    pub = os.path.join(keys_dir, "bob_public.pem")
    if not (os.path.exists(priv) and os.path.exists(pub)):
        anahtar_uret("bob", keys_dir)

def pack_hashes(hash_list):
    out = struct.pack(">I", len(hash_list))
    for h in hash_list:
        out += h
    return out

def unpack_hashes(buf):
    """
    Tek bir pack_hashes buffer'indan hash listesi dondurur.
    Eger buf formati hataliysa ValueError atar.
    """
    if len(buf) < 4:
        raise ValueError("Bozuk veri: uzunluk alani yok.")
    n = struct.unpack(">I", buf[:4])[0]
    expected = 4 + 32 * n
    if len(buf) != expected:
        raise ValueError("Bozuk veri: uzunluk uyusmuyor.")
    hashes = [buf[4+i*32:4+(i+1)*32] for i in range(n)]
    return hashes

def unpack_two_packs(buf):
    """
    Iki tane pack_hashes()'in ard arda kondugu buffer'i parse eder.
    Returns (listA, listB)
    """
    if len(buf) < 4:
        raise ValueError("Too short for first pack")
    n1 = struct.unpack(">I", buf[:4])[0]
    off = 4
    need1 = 32 * n1
    if len(buf) < off + need1 + 4:
        raise ValueError("Buffer too short for first pack")
    list_a = [buf[off+i*32:off+(i+1)*32] for i in range(n1)]
    off += need1
    if len(buf) < off + 4:
        raise ValueError("No second pack length")
    n2 = struct.unpack(">I", buf[off:off+4])[0]
    off += 4
    need2 = 32 * n2
    if len(buf) != off + need2:
        raise ValueError("Second pack size mismatch")
    list_b = [buf[off+i*32:off+(i+1)*32] for i in range(n2)]
    return list_a, list_b

def recv_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Baglanti kesildi.")
        data += chunk
    return data

def recv_packet(sock):
    hdr = recv_exact(sock, 4)
    length = struct.unpack(">I", hdr)[0]
    return recv_exact(sock, length)

def send_packet(sock, payload: bytes):
    sock.sendall(struct.pack(">I", len(payload)) + payload)

# --- Ses Enrollment Kalici Dosyasi ---
def save_enrollment(hash_list):
    os.makedirs(STORE_DIR, exist_ok=True)
    with open(STORE_FILE, "wb") as f:
        f.write(pack_hashes(hash_list))

def load_enrollment():
    if not os.path.exists(STORE_FILE):
        return None
    with open(STORE_FILE, "rb") as f:
        buf = f.read()
    return unpack_hashes(buf)

# --- Haber Enrollment Kalici Dosyasi (PERSISTENT) ---
def save_haber_enrollment(hash_list):
    os.makedirs(HABER_DIR, exist_ok=True)
    payload = pack_hashes(hash_list)
    with open(HABER_STORE_FILE, "wb") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())

def load_haber_enrollment():
    if not os.path.exists(HABER_STORE_FILE):
        return []
    with open(HABER_STORE_FILE, "rb") as f:
        buf = f.read()
        if not buf:
            return []
    try:
        hashes = unpack_hashes(buf)
    except Exception:
        return []
    return hashes

# --- AES-GCM ---
def aes_gcm_decrypt(p1: bytes, nonce: bytes, tag: bytes, ciphertext: bytes) -> bytes:
    cipher = AES.new(p1, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)

# --- Yardimci: ham icerikten 8-byte bloklar icin sha256 uret ---
def compute_block_hashes_from_raw(data: bytes, block_size: int = 8):
    if not data:
        return []
    blocks = [data[i:i+block_size] for i in range(0, len(data), block_size)]
    hashes = [hashlib.sha256(b).digest() for b in blocks]
    return hashes

def handle_client(conn):
    # 1) RSA public gonder
    server_pub = yukle_kamu("bob", "anahtarlar").export_key()
    send_packet(conn, server_pub)

    # 2) RSA-OAEP ile sifreli P1 al
    enc_p1 = recv_packet(conn)
    bob_priv = yukle_ozel("bob", "anahtarlar")
    rsa_cipher = PKCS1_OAEP.new(bob_priv)
    try:
        p1 = rsa_cipher.decrypt(enc_p1)
    except Exception:
        send_packet(conn, b"\x00RSA decrypt failed")
        return

    # 3) Sifreli mesaji al
    frame = recv_packet(conn)
    if len(frame) < 1 + 12 + 16 + 4:
        send_packet(conn, b"\x00Bad frame")
        return

    msg_type = frame[0]
    nonce    = frame[1:13]
    tag      = frame[13:29]
    ct_len   = struct.unpack(">I", frame[29:33])[0]
    if len(frame) != 33 + ct_len:
        send_packet(conn, b"\x00Bad frame size")
        return
    ct       = frame[33:33+ct_len]

    # 4) AES-GCM decrypt
    try:
        plaintext = aes_gcm_decrypt(p1, nonce, tag, ct)
    except Exception:
        send_packet(conn, b"\x00AES decrypt failed")
        return

    # debug: gelen plaintext boyutu
    print(f"[SERVER] Received plaintext {len(plaintext)} bytes for msg_type={msg_type}")

    # 5) payload: hash bloklari
    try:
        if msg_type == 5:
            # news-compare: expect two packed lists
            try:
                list_a, list_b = unpack_two_packs(plaintext)
                hash_list = (list_a, list_b)
            except Exception as e:
                # fallback: try to split plaintext in half and compute hashes for each half
                print("[SERVER] unpack_two_packs failed, attempting fallback for raw data:", e)
                mid = len(plaintext) // 2
                raw_a = plaintext[:mid]
                raw_b = plaintext[mid:]
                list_a = compute_block_hashes_from_raw(raw_a)
                list_b = compute_block_hashes_from_raw(raw_b)
                hash_list = (list_a, list_b)
        else:
            try:
                hash_list = unpack_hashes(plaintext)
            except Exception as e:
                # Eger paketlenmis hash beklenmiyorsa (bazi client'lar dogrudan dosya icerik gondermis olabilir),
                # plaintext'den 8-byte bloklarla SHA256 hesapla (fallback).
                print("[SERVER] unpack_hashes failed, using raw-data fallback for news/other. Err:", e)
                hash_list = compute_block_hashes_from_raw(plaintext)
    except Exception as e:
        send_packet(conn, b"\x00Bad payload")
        print("[SERVER] Bad payload (outer):", e)
        return

    # --- Routing ---
    if msg_type == 1:
        save_enrollment(hash_list)
        send_packet(conn, b"\x01Enrolled")
        print(f"[ENROLL] {len(hash_list)} blok kaydedildi -> {STORE_FILE}")

    elif msg_type == 2:
        enrolled = load_enrollment()
        if enrolled is None:
            send_packet(conn, b"\x00No enrollment")
            print("[VERIFY] Enrollment yok.")
            return

        m = min(len(enrolled), len(hash_list))
        same = sum(1 for i in range(m) if enrolled[i] == hash_list[i])
        ratio = same / m if m > 0 else 0.0
        ok = ratio >= THRESHOLD

        msg = f"verify ratio={ratio:.3f} threshold={THRESHOLD:.2f}".encode()
        send_packet(conn, (b"\x01" if ok else b"\x00") + msg)
        print(f"[VERIFY] {same}/{m} eslesti (ratio={ratio:.3f}) -> {'OK' if ok else 'FAIL'}")

    elif msg_type == 3:
        # Haber enroll: hash_list burda list of hashes olmali (fallback ile olustuysa da olur)
        save_haber_enrollment(hash_list)
        check_loaded = load_haber_enrollment()
        loaded_n = len(check_loaded)
        send_packet(conn, b"\x01News enrolled")
        print(f"[NEWS ENROLL] {len(hash_list)} hash kaydedildi -> {HABER_STORE_FILE} (tekrar okundu: {loaded_n})")

    elif msg_type == 4:
        enrolled = load_haber_enrollment()
        if not enrolled:
            send_packet(conn, b"\x00No news enrollment")
            print("[NEWS VERIFY] Enrollment yok veya kayit dosyasi bos/bozuk.")
            return

        # Birinci hash degerlerini diagnostik icin yazdir
        e0 = enrolled[0].hex()[:16] if enrolled else "YOK"
        i0 = hash_list[0].hex()[:16] if hash_list else "YOK"
        print(f"[NEWS VERIFY] Kayitli: {len(enrolled)} hash | Gelen: {len(hash_list)} hash")
        print(f"[NEWS VERIFY] Kayitli[0]: {e0}... | Gelen[0]: {i0}...")

        # Birebir eslesme kontrolu (exact)
        if len(hash_list) != len(enrolled):
            ok = False
            print(f"[NEWS VERIFY] FARKLI — hash sayisi uyusmuyor ({len(enrolled)} vs {len(hash_list)})")
        elif hash_list == enrolled:
            ok = True
            print(f"[NEWS VERIFY] ESLESME BASARILI — tum {len(enrolled)} hash birebir ayni.")
        else:
            ok = False
            # Kac hash farkli olduğunu bul
            diff_count = sum(1 for a, b in zip(enrolled, hash_list) if a != b)
            print(f"[NEWS VERIFY] FARKLI — {diff_count}/{len(enrolled)} hash uyusmuyor.")

        msg = f"news verify: {'SAME' if ok else 'DIFFERENT'} (enrolled={len(enrolled)}, incoming={len(hash_list)})".encode()
        send_packet(conn, (b"\x01" if ok else b"\x00") + msg)
        print(f"[NEWS VERIFY] Sonuc: {'SAME' if ok else 'DIFFERENT'}")


    elif msg_type == 5:
        # burada hash_list == (list_a, list_b)
        list_a, list_b = hash_list
        ok = (list_a == list_b)
        msg = f"news compare: {'SAME' if ok else 'DIFFERENT'} (lenA={len(list_a)}, lenB={len(list_b)})".encode()
        send_packet(conn, (b"\x01" if ok else b"\x00") + msg)
        print(f"[NEWS COMPARE] lenA={len(list_a)} lenB={len(list_b)} -> {'SAME' if ok else 'DIFFERENT'}")

    else:
        send_packet(conn, b"\x00Unknown msg_type")

def start_server(host=HOST, port=PORT):
    ensure_keys()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Allow quick reuse of address (mitigates WinError 10048 in many cases)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)
        print(f"[SERVER] {host}:{port} dinlemede. CTRL+C ile cik.")
        try:
            while True:
                conn, addr = s.accept()
                with conn:
                    print(f"[SERVER] Baglanti: {addr}")
                    try:
                        handle_client(conn)
                    except Exception as e:
                        print("[SERVER] Hata:", e)
        except KeyboardInterrupt:
            print("[SERVER] Durduruldu.")

if __name__ == "__main__":
    start_server()
