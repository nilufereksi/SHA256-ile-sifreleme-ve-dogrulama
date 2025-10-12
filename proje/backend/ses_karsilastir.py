import librosa
import numpy as np

def mfcc_cek(dosya_yolu, n_mfcc=13):
    y, sr = librosa.load(dosya_yolu, sr=None)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return np.mean(mfcc.T, axis=0)

def ses_benzet(dosya1, dosya2, esik=50):
    mfcc1 = mfcc_cek(dosya1)
    mfcc2 = mfcc_cek(dosya2)
    fark = np.linalg.norm(mfcc1 - mfcc2)

    print(f"[i] MFCC farkı: {fark:.2f}")
    return fark < esik
