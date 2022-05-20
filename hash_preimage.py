import hashlib
import os

def hash_preimage(target_string):
    if not all( [x in '01' for x in target_string ] ):
        print( "Input should be a string of bits" )
        return

    nonce = b'\x00'
    str_len = len(target_string)

    while True:
        nonce = os.urandom(str_len)

        n_hex = hashlib.sha256(nonce).hexdigest()
        n_int = int(n_hex, 16)

        code = bin(n_int)[-len(nonce):]

        if code == target_string:
            break

    return nonce



