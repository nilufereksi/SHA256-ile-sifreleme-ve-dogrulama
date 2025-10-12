import os
import hashlib
from rsa_keys import (
    yukle_kamu, yukle_ozel,
    sifrele_bloklar, desifrele_bloklar,
    bloklari_dosyaya_kaydet, dosyadan_bloklari_oku,
    public_key_fingerprint
)

# --- DİNAMİK DOSYA YOLLARI ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VERILER_DIR = os.path.join(PROJECT_DIR, "veriler")

# "veriler" klasörü yoksa oluştur (hata önler)
os.makedirs(VERILER_DIR, exist_ok=True)

# Dosya yollarını oluştur
HABER_DOSYASI = os.path.join(VERILER_DIR, "haber.txt")
HASH_DOSYASI = os.path.join(VERILER_DIR, "haber_hash.txt")  # şifreli hash burada saklanacak

def haber_hash_olustur(haber_dosyasi=HABER_DOSYASI, alici="bob"):
    if not os.path.exists(haber_dosyasi):
        print(f"Haber dosyası '{haber_dosyasi}' bulunamadı.")
        return False

    with open(haber_dosyasi, "r", encoding="utf-8", errors="ignore") as f:
        haber_metni = f.read()

    # SHA256 hash (bytes)
    haber_hash = hashlib.sha256(haber_metni.encode("utf-8")).digest()

    # Anahtar yükle (alıcı Bob'un public anahtarı)
    bob_public = yukle_kamu(alici)

    # Hash tek blok olduğundan listeye koy
    encrypted_blocks = sifrele_bloklar([haber_hash], bob_public)

    # Public key fingerprint (dosyaya ekle)
    public_key_bytes = bob_public.export_key()
    bloklari_dosyaya_kaydet(HASH_DOSYASI, encrypted_blocks, public_key_bytes)

    print(f"Haber hash'i şifrelendi ve '{HASH_DOSYASI}' dosyasına kaydedildi.")
    return True

def haber_dogrula(haber_dosyasi=HABER_DOSYASI, hash_dosyasi=HASH_DOSYASI, alici="bob"):
    if not os.path.exists(haber_dosyasi) or not os.path.exists(hash_dosyasi):
        print("Haber dosyası veya şifreli hash dosyası bulunamadı.")
        return False

    with open(haber_dosyasi, "r", encoding="utf-8", errors="ignore") as f:
        haber_metni = f.read()

    # Kaydedilmiş şifreli hash ve fingerprint oku
    try:
        sifreli_bloklar, file_fp = dosyadan_bloklari_oku(hash_dosyasi)
    except Exception as e:
        print("Şifreli hash dosyası okunamadı:", e)
        return False

    bob_private = yukle_ozel(alici)
    bob_pub_bytes = bob_private.publickey().export_key()
    bob_fp = public_key_fingerprint(bob_pub_bytes)

    if file_fp != bob_fp:
        print("UYARI: Şifreli hash dosyasındaki public key fingerprint ile mevcut anahtar uyuşmuyor.")
        return False

    # Şifre çözme
    try:
        cozulmus_hashler = desifrele_bloklar(sifreli_bloklar, bob_private)
    except Exception as e:
        print("Şifre çözme hatası:", e)
        return False

    if len(cozulmus_hashler) != 1:
        print("Beklenmeyen blok sayısı, hash doğrulaması başarısız.")
        return False

    # Yeni hash hesapla
    yeni_hash = hashlib.sha256(haber_metni.encode("utf-8")).digest()

    if yeni_hash == cozulmus_hashler[0]:
        print(" Haber doğrulandı. İçerik değişmemiş.")
        return True
    else:
        print("X Haber doğrulama başarısız! İçerik değiştirilmiş.")
        return False



if __name__ == "__main__":
    print("Haber hash oluşturuluyor ve şifreleniyor...")
    haber_hash_olustur()

    print("\nHaber doğrulaması yapılıyor...")
    haber_dogrula()