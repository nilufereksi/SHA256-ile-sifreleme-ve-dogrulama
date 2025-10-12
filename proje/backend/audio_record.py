import sounddevice as sd
from scipy.io.wavfile import write

def kayit_al(filename="kayit.wav", sure=5, frekans=44100):
    print(f"{sure} saniyelik ses kaydı başlıyor...")
    ses = sd.rec(int(sure * frekans), samplerate=frekans, channels=1, dtype='int16')
    sd.wait()
    write(filename, frekans, ses)
    print(f"Kayıt tamamlandı: {filename}")

if __name__ == "__main__":
    kayit_al()
