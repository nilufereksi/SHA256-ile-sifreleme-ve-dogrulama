import os
import hashlib
from audio_tools import record_audio, audio_to_blocks
from audio_hash import hash_blocks
from rsa_keys import (
    anahtar_uret, yukle_kamu, yukle_ozel,
    sifrele_bloklar, desifrele_bloklar,
    bloklari_dosyaya_kaydet, dosyadan_bloklari_oku,
    public_key_fingerprint
)

BERV_FILE = "bob_verisi.txt"

def dogrulama_yap():
    print("\nDOĞRULAMA MODU BAŞLADI...\n")

    bob_private = yukle_ozel('bob')
    bob_pub_bytes = bob_private.publickey().export_key()
    bob_fp = public_key_fingerprint(bob_pub_bytes)

    if not os.path.exists(BERV_FILE):
        print(f"Hata: '{BERV_FILE}' bulunamadı.")
        return

    record_audio("yeni_kayit.wav", duration=3)

    try:
        sifreli_bloklar, file_fp = dosyadan_bloklari_oku(BERV_FILE)
    except Exception as e:
        print("Dosya okunamadı:", e)
        return

    if file_fp != bob_fp:
        print("UYARI: 'bob_verisi.txt' içindeki public-key fingerprint ile bu makinadaki bob anahtarı eşleşmiyor.")
        print("Dosya eski bir anahtarla şifrelenmiş olabilir. Lütfen temiz bir başlangıç yapın.")
        return

    try:
        eski_hashler = desifrele_bloklar(sifreli_bloklar, bob_private)
    except ValueError as e:
        print("Şifre çözme sırasında hata:", e)
        print("Muhtemel neden: anahtar uyuşmazlığı veya dosya bozulması.")
        return

    blocks = audio_to_blocks("yeni_kayit.wav")
    yeni_hashler = hash_blocks(blocks)

    print("[✔] Karşılaştırılıyor...")
    basarili = True
    for i, (old, new) in enumerate(zip(eski_hashler, yeni_hashler)):
        if old != new:
            print(f"Blok {i} uyuşmuyor.")
            basarili = False
            break

    if basarili:
        print("\n Doğrulama başarılı. Ses dosyası değişmemiş.")
    else:
        print("\n Doğrulama başarısız. Ses dosyası değiştirilmiş veya farklı.")

def ilk_kayit_modu():
    record_audio("kayit.wav", duration=3)

    blocks = audio_to_blocks("kayit.wav")
    hashed = hash_blocks(blocks)

    os.makedirs("anahtarlar", exist_ok=True)
    if not (os.path.exists("anahtarlar/bob_private.pem") and os.path.exists("anahtarlar/bob_public.pem")):
        anahtar_uret("bob")
    bob_public = yukle_kamu("bob", "anahtarlar")
    bob_pub_bytes = bob_public.export_key()

    encrypted = sifrele_bloklar(hashed, bob_public)

    print("\nHızlı self-test başlıyor...")
    bob_priv = yukle_ozel("bob", "anahtarlar")
    try:
        dec_test = desifrele_bloklar(encrypted, bob_priv)
    except Exception as e:
        print("SELF-TEST: Şifreleme/çözme başarısız:", e)
        return
    for i, (orig, dec) in enumerate(zip(hashed, dec_test)):
        if orig != dec:
            print(f"SELF-TEST FAIL: blok {i} farklı. Yazma işlemi yapılmayacak.")
            return
    print("SELF-TEST OK: encryption->decryption aynı run içinde başarılı.")

    bloklari_dosyaya_kaydet(BERV_FILE, encrypted, bob_pub_bytes)
    print("\nİlk kayıt tamamlandı ve veriler şifrelendi.")

if __name__ == "__main__":
    if os.path.exists(BERV_FILE):
        dogrulama_yap()
    else:
        ilk_kayit_modu()
