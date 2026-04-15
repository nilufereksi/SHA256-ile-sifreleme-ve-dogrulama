import socket
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from utils import sha256_hash

def load_private_key():
    with open("private.pem", "rb") as f:
        return RSA.import_key(f.read())

def bob_client():
    # Socket bağlan
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 5000))
    print("✅ Bob: Alice'e bağlandı.")

    # Veri al
    data = client.recv(8192)  # büyük buffer
    client.close()

    # Hash ve şifreli veriyi ayır
    haber_hash, encrypted_data = data.split(b"||")

    # Private key ile çöz
    private_key = load_private_key()
    cipher_rsa = PKCS1_OAEP.new(private_key)
    decrypted_haber = cipher_rsa.decrypt(encrypted_data).decode("utf-8")

    # Hash doğrulama
    yeni_hash = sha256_hash(decrypted_haber)
    if yeni_hash == haber_hash.decode("utf-8"):
        print(" Haber doğrulandı ve çözüldü.")
        print(" İçerik:", decrypted_haber)
    else:
        print(" Haber doğrulama başarısız!")

if __name__ == "__main__":
    bob_client()
