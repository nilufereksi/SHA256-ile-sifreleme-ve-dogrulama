# HashVerify 🔐


<img width="800" height="476" alt="hashverify github" src="https://github.com/user-attachments/assets/b46b5361-58f0-4021-9714-0bc96edf3060" />


**SHA-256 tabanlı haber ve ses bütünlük doğrulama sistemi.**

HashVerify, bir metin haberinin veya ses kaydının orijinalliğini SHA-256 kriptografik hash'leri ve RSA şifreleme kullanarak doğrulayan bir masaüstü güvenlik uygulamasıdır. İçerik bir kez sisteme kaydedilir (enroll); sonraki doğrulama adımında hash'ler karşılaştırılarak manipülasyon anında tespit edilir.

---

## ✨ Özellikler

- 📰 **Haber Doğrulama** — Metin dosyaları (`.txt`) blok blok SHA-256 ile hash'lenir; kayıtlı referans hash ile karşılaştırılarak değiştirilip değiştirilmediği tespit edilir.
- 🎙 **Ses Doğrulama** — Ses kaydı bloklara bölünür, her blok hash'lenir; daha sonra kaydedilen sesin eşleşip eşleşmediği oran bazlı kontrolle anlık raporlanır.
- 🔐 **RSA + AES-GCM Şifreleme** — İstemci-sunucu iletişimi RSA-OAEP ile anahtar değişimi ve AES-GCM ile şifreli kanal üzerinden gerçekleşir.
- 🖥 **Modern GUI** — CustomTkinter tabanlı, navy-dark temalı şık arayüz.
- 🌐 **İstemci-Sunucu Mimarisi** — `server_master.py` sunucu olarak çalışır; `gui_client.py` grafiksel istemci olarak bağlanır.

---

## 🗂 Proje Yapısı

```
sha256-antigravity/
├── backend/
│   ├── server_master.py   # Hash doğrulama sunucusu (port 5000)
│   ├── gui_client.py      # CustomTkinter GUI istemcisi
│   ├── client_slave.py    # Komut satırı istemcisi (haber/ses gönderici)
│   ├── main.py            # Ses doğrulama CLI (RSA ile)
│   ├── audio_hash.py      # Ses bloklarını hash'leme
│   ├── audio_tools.py     # Ses kaydı ve blok oluşturma
│   ├── haber_hash.py      # Haber metni hash yardımcıları
│   ├── rsa_keys.py        # RSA anahtar üretimi ve işlemleri
│   └── utils.py           # Genel yardımcılar
├── txt/
│   ├── haber1.txt         # Örnek haber dosyası (orijinal)
│   └── haber2.txt         # Örnek haber dosyası (değiştirilmiş)
├── keys/                  # RSA anahtar dizini
├── requirements.txt
└── README.md
```

---

## 🚀 Kurulum

### Gereksinimler

- Python 3.9+
- Windows / macOS / Linux

### Adımlar

```bash
# 1. Repoyu klonla
git clone https://github.com/kullaniciadi/hashverify.git
cd hashverify

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. backend dizinine gir
cd backend
```

> **Not:** `pyaudio` kurulumunda sorun yaşarsanız [PyAudio Wheel](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) sayfasından sisteminize uygun `.whl` dosyasını indirerek `pip install <dosya>.whl` ile kurabilirsiniz.

---

## ▶️ Kullanım

### 1. Sunucuyu Başlat

```bash
cd backend
python server_master.py
```

Sunucu `127.0.0.1:5000` adresinde dinlemeye başlar.

### 2. GUI İstemcisini Aç

Yeni bir terminal sekmesinde:

```bash
cd backend
python gui_client.py
```

---

## 🖥 Arayüz

Uygulama üç sekmeye ayrılmıştır:

| Sekme | Açıklama |
|-------|----------|
| ⚙ Server | Sunucuyu GUI üzerinden başlatıp durdur |
| 📰 Haber | Metin dosyası enroll & verify |
| 🎙 Ses | Ses kaydı enroll & verify |

---

## 🔬 Nasıl Çalışır?

```
İstemci                          Sunucu (port 5000)
   │                                    │
   │──── RSA Public Key İste ──────────>│
   │<─── Server Public Key ─────────────│
   │                                    │
   │  AES-GCM anahtarı (P1) üret       │
   │──── RSA-OAEP(P1) Gönder ─────────>│
   │──── AES-GCM(msg_type + hash) ────>│
   │                                    │  Hash'leri depola / karşılaştır
   │<─── Sonuç (SAME / DIFFERENT) ──────│
```

### Mesaj Tipleri

| Tip | Açıklama |
|-----|----------|
| `1` | Ses enroll — hash'leri kaydet |
| `2` | Ses verify — kayıtlı hash ile karşılaştır |
| `3` | Haber enroll — metin hash'lerini kaydet |
| `4` | Haber verify — birebir hash karşılaştırması |
| `5` | İki dosya arasında anlık karşılaştırma |

---

## 📸 Ekran Görüntüleri

### ✅ Hash'ler Aynı — Doğrulama Başarılı

> Orijinal haber dosyası sisteme kaydedildikten sonra aynı dosya ile doğrulama yapıldığında tüm hash blokları eşleşir.

<!-- SCREENSHOT_SAME: GUI'de "DOGRULAMA BASARILI / SAME" çıktısının terminaldeki görüntüsü -->
<img width="841" height="95" alt="resim" src="https://github.com/user-attachments/assets/c3279403-db5c-4d81-abff-0ccc2c90e4fc" />


---

### ❌ Hash'ler Farklı — Manipülasyon Tespit Edildi

> Haber dosyasının içeriği değiştirildiğinde (tek bir karakter bile) hash blokları uyuşmaz ve sistem manipülasyonu tespit eder.

<!-- SCREENSHOT_DIFFERENT: GUI'de "DOGRULAMA BASARISIZ / DIFFERENT" çıktısının terminaldeki görüntüsü -->
<img width="840" height="89" alt="resim" src="https://github.com/user-attachments/assets/858d23ea-6bb1-4431-8d64-3f3181e3bae6" /> 

---

## 📦 Bağımlılıklar

```
customtkinter==5.2.2   # GUI
numpy                  # Sayısal işlemler
librosa                # Ses analizi
scipy                  # Sinyal işleme
sounddevice            # Ses kaydı
pyaudio                # Ses I/O
pycryptodome           # RSA / AES şifreleme
```

---

## 🔑 Güvenlik Notları

- RSA anahtarları `backend/anahtarlar/` dizininde saklanır ve `.gitignore` ile repo dışında tutulur.
- Sunucuda kayıtlı hash'ler `server_data/enrolled_hashes.bin` ve `haberler/enrolled_news_hashes.bin` dosyalarında ikili formatta tutulur; bu dosyalar da repo'ya dahil edilmez.
- Ses kaydı yalnızca yerel diskte geçici olarak tutulur, uzak sisteme gönderilmez.

---

## 📄 Lisans

Bu proje MIT Lisansı ile lisanslanmıştır.
