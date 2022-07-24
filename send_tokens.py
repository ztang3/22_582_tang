#!/usr/bin/python3

from algosdk.v2client import algod
from algosdk import mnemonic
from algosdk import transaction

# Connect to Algorand node maintained by PureStake
algod_address = "https://testnet-algorand.api.purestake.io/ps2"
algod_token = "B3SU4KcVKi94Jap2VXkK83xx38bsv95K5UZm2lab"
# algod_token = 'IwMysN3FSZ8zGVaQnoUIJ9RXolbQ5nRY62JRqF2H'
headers = {
    "X-API-Key": algod_token,
}

acl = algod.AlgodClient(algod_token, algod_address, headers)
min_balance = 100000  # https://developer.algorand.org/docs/features/accounts/#minimum-balance

address = '3QXTKNRCD2IGS3W5O4OZVCTVQEL7S2GLX2I7L25HXSWIVECN4SRVWON5OU'
secret_key = 'A5IhLGYJw420mRkgPT3J2QNrOK9tpNn8lomdTW2hS2HcLzU2Ih6QaW7ddx2ainWBF/loy76R9eunvKyKkE3kow=='


def send_tokens(receiver_pk, tx_amount):
    params = acl.suggested_params()
    gen_hash = params.gh
    first_valid_round = params.first
    tx_fee = params.min_fee
    last_valid_round = params.last

    # Your code here

    sender_pk = address

    txid = acl.send_transaction(
        transaction.PaymentTxn(address, tx_fee, first_valid_round, last_valid_round, gen_hash, receiver_pk,
                               tx_amount).sign(secret_key))

    return sender_pk, txid


# Function from Algorand Inc.
def wait_for_confirmation(client, txid):
    """
    Utility function to wait until the transaction is
    confirmed before proceeding.
    """
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print("Transaction {} confirmed in round {}.".format(txid, txinfo.get('confirmed-round')))
    return txinfo

def generate_account_with_info():
    sk, address = account.generate_account()
    return sk, address

if __name__ == '__main__':
    sk, address = generate_account_with_info()
    print(sk)
    print(address)