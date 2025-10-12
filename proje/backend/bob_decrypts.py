from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from alice_encrypts import alice_sifrele
from audio_hash import oku_ve_hash_al

def bob_coz(sifreli_veriler, bob_private_key_path="anahtarlar/bob_private.pem"):
    with open(bob_private_key_path, "rb") as f:
        private_key = RSA.import_key(f.read())

    cipher = PKCS1_OAEP.new(private_key)
    cozulmusler = []

    for veri in sifreli_veriler:
        cozulmus = cipher.decrypt(veri)
        cozulmusler.append(cozulmus)  # bytes olarak kaydet, hex yapma
    return cozulmusler

if __name__ == "__main__":
    hashler = oku_ve_hash_al()  # muhtemelen bytes listesi
    sifreli = alice_sifrele(hashler)
    cozumler = bob_coz(sifreli)

    for i in range(len(cozumler)):
        # Karşılaştırma için bytes'ı bytes ile karşılaştır
        print(f"{i+1}. çözüldü: {cozumler[i] == hashler[i]}")
