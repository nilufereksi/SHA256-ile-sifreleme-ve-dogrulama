from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from audio_hash import oku_ve_hash_al
import hashlib

def alice_sifrele(hashler, bob_public_key_path="anahtarlar/bob_public.pem"):
    with open(bob_public_key_path, "rb") as f:
        bob_key = RSA.import_key(f.read())
    
    cipher = PKCS1_OAEP.new(bob_key)

    encrypted_data = []
    for h in hashler[:5]:  # ilk 5 hash’i şifreleyelim örnek olarak
        # h ya str (hex) ya da bytes olabilir, ona göre dönüştür
        if isinstance(h, str):
            h_bytes = bytes.fromhex(h)
        else:
            h_bytes = h
        encrypted = cipher.encrypt(h_bytes)
        encrypted_data.append(encrypted)

    print(f"{len(encrypted_data)} adet şifreli veri üretildi.")
    return encrypted_data

if __name__ == "__main__":
    hashler = oku_ve_hash_al()
    sifreli = alice_sifrele(hashler)
