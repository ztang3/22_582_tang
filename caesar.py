## encode
def encrypt(key,plaintext):
    ciphertext=""
    #YOUR CODE HERE
    for c in plaintext:
        offset = key % 26
        raw_c = offset + ord(c)

        if raw_c > ord('Z'):
            offset_from_start = raw_c -  ord('Z') - 1
            raw_c = ord('A') + offset_from_start

        ciphertext += chr(raw_c)
    return ciphertext


## decode
def decrypt(key,ciphertext):
    plaintext=""
    #YOUR CODE HERE
    for c in ciphertext:
        offset = key % 26

        raw_c = ord(c) - offset

        if raw_c < ord('A'):
            offset_before_start = ord('A') - raw_c - 1
            raw_c = ord('Z') - offset_before_start

        plaintext += chr(raw_c)
    return plaintext

