import wave
import pyaudio

def record_audio(filename="kayit.wav", duration=5, channels=1, rate=44100):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=1024)

    print(f" Kayıt başlıyor ({duration} saniye)...")
    frames = []
    for _ in range(0, int(rate / 1024 * duration)):
        data = stream.read(1024)
        frames.append(data)

    print(" Kayıt tamamlandı.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

def audio_to_blocks(filepath, block_size=8):
    with wave.open(filepath, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())

    # Ses verisini bloklara ayır (her blok = 8 byte)
    return [frames[i:i+block_size] for i in range(0, len(frames), block_size) if len(frames[i:i+block_size]) == block_size]
