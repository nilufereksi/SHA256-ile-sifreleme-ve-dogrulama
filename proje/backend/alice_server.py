import socket
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from utils import sha256_hash

def load_public_key():
    with open("public.pem", "rb") as f:
        return RSA.import_key(f.read())

def alice_server():
    # Alice haber dosyasını okur
    with open("haber.txt", "r", encoding="utf-8") as f:
        haber = f.read()

    # Hash üret
    haber_hash = sha256_hash(haber)

    # Public key ile şifreleme
    public_key = load_public_key()
    cipher_rsa = PKCS1_OAEP.new(public_key)
    encrypted_data = cipher_rsa.encrypt(haber.encode("utf-8"))

    # Socket başlat
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", 5000))
    server.listen(1)
    print("✅ Alice: Bob bekleniyor...")

    conn, addr = server.accept()
    print(f"📡 Bob bağlandı: {addr}")

    # Önce hash gönder
    conn.sendall(haber_hash.encode("utf-8"))
    # Sonra şifrelenmiş veriyi gönder
    conn.sendall(b"||")  # ayraç
    conn.sendall(encrypted_data)

    print("📤 Haber Bob’a gönderildi.")
    conn.close()

if __name__ == "__main__":
    alice_server()
