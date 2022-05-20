import hashlib
import os


def hash_collision(k):
    if not isinstance(k, int):
        print("hash_collision expects an integer")
        return (b'\x00', b'\x00')
    if k < 0:
        print("Specify a positive number of bits")
        return (b'\x00', b'\x00')

    x = b'\x00'
    y = b'\x00'

    memory = {}

    while True:
        b = os.urandom(k)

        b_hex = hashlib.sha256(b).hexdigest()
        b_int = int(b_hex, 16)

        final_k = bin(b_int)[-k:]

        if final_k not in memory:
            memory[final_k] = b

        else:
            x = b
            y = memory[final_k]
            break

    return (x, y)
