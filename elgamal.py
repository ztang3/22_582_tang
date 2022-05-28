import random

from params import p
from params import g

def keygen():
    a = random.randint(1, p)
    h = pow(g, a, p)

    pk = h
    sk = a
    return pk, sk


def encrypt(pk,m):
    h = pk
    r = random.randint(1, p)

    c1 = pow(g, r, p)
    c2 = (pow(h, r, p) * (m % p)) % p

    return [c1, c2]

def decrypt(sk,c):
    (c1, c2) = c
    a = sk

    m = ((c2 % p) * pow(c1, -1 * a, p)) % p

    return m





