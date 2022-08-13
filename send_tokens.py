#!/usr/bin/python3

import time
from algosdk.v2client import algod
from algosdk.v2client import indexer
from algosdk import account
from algosdk.future import transaction


def connect_to_algo(connection_type=''):
    # Connect to Algorand node maintained by PureStake
    algod_token = "B3SU4KcVKi94Jap2VXkK83xx38bsv95K5UZm2lab"

    if connection_type == "indexer":
        # TODO: return an instance of the v2client indexer. This is used for checking payments for tx_id's
        algod_address = "https://testnet-algorand.api.purestake.io/idx2"
        return indexer.IndexerClient(indexer_token=algod_token, indexer_address=algod_address)
    else:
        # TODO: return an instance of the client for sending transactions
        # Tutorial Link: https://developer.algorand.org/tutorials/creating-python-transaction-purestake-api/
        algod_address = "https://testnet-algorand.api.purestake.io/ps2"
        return algod.AlgodClient(algod_token, algod_address, headers={'X-Api-key': algod_token})
    return None


def send_tokens_algo(acl, sender_sk, txes):
    params = acl.suggested_params()

    # TODO: You might want to adjust the first/last valid rounds in the suggested_params
    #       See guide for details

    # TODO: For each transaction, do the following:
    #       - Create the Payment transaction
    #       - Sign the transaction

    # TODO: Return a list of transaction id's

    sender_pk = account.address_from_private_key(sender_sk)
    tx_ids = []

    try:
        params.first
    except Exception as e:
        params.first = 0

    constant = 800

    for i, tx in enumerate(txes):
        params.last = params.first + constant + i

        unsigned_tx = transaction.PaymentTxn(sender_pk, params, tx['receiver_pk'], tx['amount'])

        # params.first += 1
        # TODO: Sign the transaction
        signed_tx = unsigned_tx.sign(sender_sk)

        try:
            print(f"Sending {tx['amount']} microalgo from {sender_pk} to {tx['receiver_pk']}")

            # TODO: Send the transaction to the testnet
            try:
                time.sleep(4)
                try:
                    tx_id = acl.send_transaction(signed_tx)
                except Exception as e:
                    print(e)

                time.sleep(2.0)

                try:
                    txinfo = wait_for_confirmation_algo(acl, txid=tx_id)
                except Exception as e:
                    print(e)

                print(f"Sent {tx['amount']} microalgo in transaction: {tx_id}\n")
            except Exception as e:
                print("send algo try failed")
                tx_id = None
            tx_ids.append(tx_id)
        except Exception as e:
            print(e)

    return tx_ids


# Function from Algorand Inc.
def wait_for_confirmation_algo(client, txid):
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


##################################

from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import TransactionNotFound
import json
import progressbar


def connect_to_eth():
    IP_ADDR = '3.23.118.2'  # Private Ethereum
    PORT = '8545'

    w3 = Web3(Web3.HTTPProvider('http://' + IP_ADDR + ':' + PORT))
    w3.middleware_onion.inject(geth_poa_middleware,
                               layer=0)  # Required to work on a PoA chain (like our private network)
    w3.eth.account.enable_unaudited_hdwallet_features()
    if w3.isConnected():
        return w3
    else:
        print("Failed to connect to Eth")
        return None


def wait_for_confirmation_eth(w3, tx_hash):
    print("Waiting for confirmation")
    widgets = [progressbar.BouncingBar(marker=progressbar.RotatingMarker(), fill_left=False)]
    i = 0
    with progressbar.ProgressBar(widgets=widgets, term_width=1) as progress:
        while True:
            i += 1
            progress.update(i)
            try:
                receipt = w3.eth.get_transaction_receipt(tx_hash)
            except TransactionNotFound:
                continue
            break
    return receipt


####################
def send_tokens_eth(w3, sender_sk, txes):
    sender_account = w3.eth.account.privateKeyToAccount(sender_sk)
    sender_pk = sender_account._address

    # TODO: For each of the txes, sign and send them to the testnet
    # Make sure you track the nonce -locally-

    tx_ids = []
    nums = w3.eth.get_transaction_count(sender_pk, "pending")

    for i, tx in enumerate(txes):
        # Your code here

        signed_tx = w3.eth.account.sign_transaction({
            'nonce': nums + i,
            'gasPrice': w3.eth.gas_price,
            'gas': w3.eth.estimate_gas({'from': sender_pk, 'to': tx["receiver_pk"], 'data': b'', 'amount':  tx["amount"]}),
            'to': tx["receiver_pk"],
            'value':  tx["amount"],
            'data': b''}, sender_sk)
        try:
            id = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        except Exception as e:
            id = None

        tx_ids.append(id)

    return tx_ids
