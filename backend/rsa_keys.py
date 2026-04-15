from Crypto.PublicKey import RSA
import os

# --- DİNAMİK ANAHTAR KLASÖRÜ ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ANAHTAR_DIR = os.path.join(PROJECT_DIR, "anahtarlar")
os.makedirs(ANAHTAR_DIR, exist_ok=True)  # klasörü oluştur

def anahtar_uret(isim="default", klasor=ANAHTAR_DIR):
    """Anahtar üret ve verilen klasöre kaydet"""
    os.makedirs(klasor, exist_ok=True)  # klasörü oluştur
    key = RSA.generate(2048)

    private_key = key.export_key()
    public_key = key.publickey().export_key()

    private_path = os.path.join(klasor, f"{isim}_private.pem")
    public_path = os.path.join(klasor, f"{isim}_public.pem")

    with open(private_path, "wb") as f:
        f.write(private_key)

    with open(public_path, "wb") as f:
        f.write(public_key)

    print(f"Anahtarlar üretildi: {private_path}, {public_path}")

def yukle_kamu(isim="default", klasor=ANAHTAR_DIR):
    """Public key yükle"""
    return RSA.import_key(open(os.path.join(klasor, f"{isim}_public.pem"), "rb").read())

def yukle_ozel(isim="default", klasor=ANAHTAR_DIR):
    """Private key yükle"""
    return RSA.import_key(open(os.path.join(klasor, f"{isim}_private.pem"), "rb").read())


if __name__ == "__main__":
    anahtar_uret("bob")  # Örnek olarak Bob'un anahtarlarını üret
