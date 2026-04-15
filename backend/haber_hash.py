import hashlib
import os

def haber_hash_olustur(haber_dosyasi="haber.txt", hash_dosyasi="haber_hash.txt"):
    if not os.path.exists(haber_dosyasi):
        print(f"Haber dosyası '{haber_dosyasi}' bulunamadı.")
        return False

    with open(haber_dosyasi, "r", encoding="utf-8", errors="ignore") as f:
        haber_metni = f.read()

    haber_hash = hashlib.sha256(haber_metni.encode("utf-8")).hexdigest()

    with open(hash_dosyasi, "w") as f:
        f.write(haber_hash)

    print(f"Haber için SHA256 hash oluşturuldu ve '{hash_dosyasi}' dosyasına kaydedildi.")
    return True

def haber_dogrula(haber_dosyasi="haber.txt", hash_dosyasi="haber_hash.txt"):
    if not os.path.exists(haber_dosyasi) or not os.path.exists(hash_dosyasi):
        print("Haber dosyası veya hash dosyası bulunamadı.")
        return False

    with open(haber_dosyasi, "r", encoding="utf-8", errors="ignore") as f:
        haber_metni = f.read()

    with open(hash_dosyasi, "r") as f:
        kayitli_hash = f.read().strip()

    if len(kayitli_hash) != 64:
        print(f"Uyarı: '{hash_dosyasi}' dosyasındaki hash beklenen formatta değil.")
        return False

    yeni_hash = hashlib.sha256(haber_metni.encode("utf-8")).hexdigest()

    if yeni_hash == kayitli_hash:
        print(" Haber doğrulandı. İçerik değişmemiş.")
        return True
    else:
        print(" Haber doğrulama başarısız! İçerik değiştirilmiş.")
        return False

if __name__ == "__main__":
    print("Hash oluşturuluyor...")
    haber_hash_olustur()

    print("\nDoğrulama yapılıyor...")
    haber_dogrula()
