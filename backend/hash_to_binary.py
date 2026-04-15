def hex_to_binary(hash_listesi):
    binary_list = []
    for h in hash_listesi:
        binary = bin(int(h, 16))[2:].zfill(256)  # 256 bit uzunluğunda binary
        binary_list.append(binary)
    return binary_list

if __name__ == "__main__":
    from audio_hash import oku_ve_hash_al

    hashler = oku_ve_hash_al()
    binary_hashler = hex_to_binary(hashler)

    for i, b in enumerate(binary_hashler[:3]):
        print(f"{i+1}. binary: {b[:64]}...")  # ilk 64 bit göster
