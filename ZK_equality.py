from zksk import Secret, DLRep
from zksk import utils

def ZK_equality(G,H):

    seed1 = utils.get_random_num(bits=128)
    r1 = Secret(seed1)

    seed2 = utils.get_random_num(bits=128)
    r2 = Secret(seed2)

    seed3 = utils.get_random_num(bits=128)
    m = Secret(seed3)

    C1 = r1.value * G
    D1 = r2.value * G

    C2 = r1.value * H + m.value * G
    D2 = r2.value * H + m.value * G

    zk_proof = (DLRep(C1, r1 * G)
                & DLRep(C2, r1 * H + m * G)
                & DLRep(D1, r2 * G)
                & DLRep(D2, r2 * H + m * G)).prove()


    return (C1,C2), (D1,D2), zk_proof

