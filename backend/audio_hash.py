import wave
import hashlib

def oku_ve_hash_al(dosya_adi="kayit.wav"):
    with wave.open(dosya_adi, 'rb') as wav_file:
        frames = wav_file.readframes(wav_file.getnframes())
        byte_data = bytearray(frames)
        
    print(f"Toplam byte uzunlugu: {len(byte_data)}")
    
    hash_listesi = []

    for i in range(0, len(byte_data), 8):
        parca = byte_data[i:i+8]
        if len(parca) < 8:
            break  # son parca eksikse alma
        sha = hashlib.sha256(parca).digest()
        hash_listesi.append(sha)

    print(f"{len(hash_listesi)} adet 8 byte'lik hash uretildi.")
    return hash_listesi

import hashlib

def hash_blocks(blocks):
    hashes = []
    for block in blocks:
        h = hashlib.sha256(block).digest()
        hashes.append(h)
    return hashes


if __name__ == "__main__":
    hashler = oku_ve_hash_al()
    for i, h in enumerate(hashler[:5]):
        print(f"{i+1}. hash: {h}")

import hashlib

def hash_text_file(file_path):
    hashes = []
    try:
        with open(file_path, "rb") as f:  # binary oku
            content = f.read()

        # Icerigi 8 byte'lik bloklara bol
        for i in range(0, len(content), 8):
            block = content[i:i+8]
            if len(block) < 8:
                continue
            h = hashlib.sha256(block).digest()
            hashes.append(h)

        print(f"[DEBUG] {file_path}: {len(hashes)} hash uretildi.")
        return hashes

    except Exception as e:
        print(f"[ERROR] {file_path} hash alinirken hata: {e}")
        return []

