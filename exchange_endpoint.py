from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from flask import jsonify
import json
import eth_account
import algosdk
from algosdk import mnemonic
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only
from datetime import datetime
import math
import sys
import time
import traceback
from web3 import Web3

# TODO: make sure you implement connect_to_algo, send_tokens_algo, and send_tokens_eth
from send_tokens import connect_to_algo, connect_to_eth, send_tokens_algo, send_tokens_eth

from models import Base, Order, TX, Log

engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

""" Pre-defined methods (do not need to change) """


@app.before_request
def create_session():
    g.session = scoped_session(DBSession)


@app.teardown_appcontext
def shutdown_session(response_or_exc):
    sys.stdout.flush()
    g.session.commit()
    g.session.remove()


def connect_to_blockchains():
    try:
        # If g.acl has not been defined yet, then trying to query it fails
        acl_flag = False
        g.acl
    except AttributeError as ae:
        acl_flag = True

    try:
        if acl_flag or not g.acl.status():
            # Define Algorand client for the application
            g.acl = connect_to_algo()
    except Exception as e:
        print("Trying to connect to algorand client again")
        print(traceback.format_exc())
        g.acl = connect_to_algo()

    try:
        icl_flag = False
        g.icl
    except AttributeError as ae:
        icl_flag = True

    try:
        if icl_flag or not g.icl.health():
            # Define the index client
            g.icl = connect_to_algo(connection_type='indexer')
    except Exception as e:
        print("Trying to connect to algorand indexer client again")
        print(traceback.format_exc())
        g.icl = connect_to_algo(connection_type='indexer')

    try:
        w3_flag = False
        g.w3
    except AttributeError as ae:
        w3_flag = True

    try:
        if w3_flag or not g.w3.isConnected():
            g.w3 = connect_to_eth()
    except Exception as e:
        print("Trying to connect to web3 again")
        print(traceback.format_exc())
        g.w3 = connect_to_eth()


""" End of pre-defined methods """

""" Helper Methods (skeleton code for you to implement) """


def log_message(d):
    log_info = Log(message=json.dumps(d), logtime=datetime.now())
    g.session.add(log_info)
    g.session.commit()


def get_algo_keys():
    # TODO: Generate or read (using the mnemonic secret)
    # the algorand public/private keys
    algo_sk = "1N1zudafaLsI7XUPhRBNl4rF5suXIgzA7MI2p9LAaV1AoU0lCWH6NwzewSghdbkLveyCN6MbP9DQK8L+GDcIZw=="
    algo_pk = "ICQU2JIJMH5DODG6YEUCC5NZBO66ZARXUMNT7UGQFPBP4GBXBBTUFDCSYY"
    return algo_sk, algo_pk


def get_eth_keys(filename="eth_mnemonic.txt"):
    # TODO: Generate or read (using the mnemonic secret)
    # the ethereum public/private keys

    eth_pk = '0x03Ea3A19E221990fee05dD3cFA5f2D215b9924D3'
    eth_sk = b'\xdb\xdc\xba\xe6\xa5b\x85u\xd7\r\xd3ohk\x80E\xb8\x14\xad(\x12\xc1U\x98\xe4\x81\xe6\xa1\x98\x94\xf5\xd1'
    return eth_sk, eth_pk


def fill_order(order, txes=[]):
    # TODO:
    # Match orders (same as Exchange Server II)
    time.sleep(3)
    orders = g.session.query(Order).filter(Order.creator == None).all()

    for query_ord in orders:
        if query_ord.filled is None and query_ord.sell_currency == order.buy_currency and query_ord.buy_currency == order.sell_currency and query_ord.sell_amount / query_ord.buy_amount >= order.buy_amount / order.sell_amount:
            order.filled = datetime.now()
            query_ord.filled = datetime.now()
            order.counterparty_id = query_ord.id
            query_ord.counterparty_id = order.id
            g.session.commit()

            if (order.sell_amount < query_ord.buy_amount):
                new_order = {
                    'buy_currency': query_ord.buy_currency,
                    'sell_currency': query_ord.sell_currency,
                    'buy_amount': query_ord.buy_amount - order.sell_amount,
                    'sell_amount': int((query_ord.buy_amount - order.sell_amount) * (
                            query_ord.sell_amount / query_ord.buy_amount)) + 1,
                    'sender_pk': query_ord.sender_pk,
                    'receiver_pk': query_ord.receiver_pk,
                    'creator_id': query_ord.id
                }

                new_order_recur = Order(**{f: new_order[f] for f in
                                           ['buy_currency', 'sell_currency', 'sender_pk', 'receiver_pk',
                                            'buy_amount', 'sell_amount',
                                            'creator_id']})

                g.session.add(new_order_recur)
                g.session.commit()

            elif (query_ord.buy_amount < order.sell_amount):
                buy_amount = int(
                    (order.buy_amount / order.sell_amount) * (order.sell_amount - query_ord.buy_amount))
                if buy_amount != 0:
                    new_order = {
                        'buy_currency': order.buy_currency,
                        'sell_currency': order.sell_currency,
                        'buy_amount': buy_amount,
                        'sell_amount': order.sell_amount - query_ord.buy_amount,
                        'sender_pk': order.sender_pk,
                        'receiver_pk': order.receiver_pk,
                        'creator_id': order.id
                    }

                    new_order_recur = Order(**{f: new_order[f] for f in
                                               ['sender_pk', 'receiver_pk', 'buy_currency', 'sell_currency',
                                                'buy_amount',
                                                'sell_amount',
                                                'creator_id']})
                    g.session.add(new_order_recur)
                    g.session.commit()

            if order.sell_currency == "Algorand":
                a_ord = query_ord
                e_ord = order
            else:
                a_ord = order
                e_ord = query_ord

            a_tx = {
                "platform": "Algorand",
                "amount": a_ord.buy_amount,
                "receiver_pk": a_ord.receiver_pk,
                "order_id": a_ord.id
            }

            e_tx = {
                "platform": "Ethereum",
                "amount": e_ord.buy_amount,
                "receiver_pk": e_ord.receiver_pk,
                "order_id": e_ord.id
            }

            if a_ord.child:
                a_tx["amount"] = a_tx["amount"] - a_ord.child[0].buy_amount
            if e_ord.child:
                e_tx["amount"] = e_tx["amount"] - e_ord.child[0].buy_amount

            txes.append(e_tx)
            txes.append(a_tx)
            break


def execute_txes(txes):
    if txes is None:
        return True
    if len(txes) == 0:
        return True
    print(f"Trying to execute {len(txes)} transactions")
    print(f"IDs = {[tx['order_id'] for tx in txes]}")
    eth_sk, eth_pk = get_eth_keys()
    algo_sk, algo_pk = get_algo_keys()

    if not all(tx['platform'] in ["Algorand", "Ethereum"] for tx in txes):
        print("Error: execute_txes got an invalid platform!")
        print(tx['platform'] for tx in txes)

    algo_txes = [tx for tx in txes if tx['platform'] == "Algorand"]
    eth_txes = [tx for tx in txes if tx['platform'] == "Ethereum"]

    # TODO:
    #       1. Send tokens on the Algorand and eth testnets, appropriately
    #          We've provided the send_tokens_algo and send_tokens_eth skeleton methods in send_tokens.py
    #       2. Add all transactions to the TX table

    a_ids = send_tokens_algo(g.acl, algo_sk, algo_txes)
    execute(a_ids,algo_txes)

    e_ids = send_tokens_eth(g.w3, eth_sk, eth_txes)
    execute(e_ids,eth_txes)

def execute(ids, txes):
    for i in range(len(txes)):
        if ids[i] is not None:
            tx = txes[i]
            tx['tx_id'] = ids[i]
            g.session.add(TX(**{attr: tx[attr] for attr in ['platform', 'receiver_pk', 'order_id', 'tx_id']}))
            g.session.commit()


def check_back(order):
    if order.sell_currency == "Algorand":
        try:
            transactions = g.icl.search_transactions(txid=order.tx_id)
            try:
                if not 'transactions' in transactions.keys():
                    return False
            except Exception as e:
                return False
            for tx in transactions["transactions"]:
                if 'payment-transaction' in tx.keys() and tx['payment-transaction']['amount'] == order.sell_amount and tx['sender'] == order.sender_pk:
                    return True
        except Exception:
            return False
    elif order.sell_currency == "Ethereum":
        try:
            tx = g.w3.eth.get_transaction(order.tx_id)
            if tx['value'] == order.sell_amount and tx['from'] == order.sender_pk:
                return True
        except Exception:
            return False
    return False


""" End of Helper methods"""


@app.route('/address', methods=['POST'])
def address():
    if request.method == "POST":
        content = request.get_json(silent=True)
        if 'platform' not in content.keys():
            print(f"Error: no platform provided")
            return jsonify("Error: no platform provided")
        if not content['platform'] in ["Ethereum", "Algorand"]:
            print(f"Error: {content['platform']} is an invalid platform")
            return jsonify(f"Error: invalid platform provided: {content['platform']}")

        if content['platform'] == "Ethereum":
            # Your code here
            eth_sk, eth_pk = get_eth_keys()
            return jsonify(eth_pk)
        if content['platform'] == "Algorand":
            # Your code here
            algo_sk, algo_pk = get_algo_keys()

            return jsonify(algo_pk)


@app.route('/trade', methods=['POST'])
def trade():
    print("In trade", file=sys.stderr)
    connect_to_blockchains()
    if request.method == "POST":
        content = request.get_json(silent=True)
        columns = ["buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform", "tx_id", "receiver_pk"]
        fields = ["sig", "payload"]
        error = False
        for field in fields:
            if not field in content.keys():
                print(f"{field} not received by Trade")
                error = True
        if error:
            print(json.dumps(content))
            return jsonify(False)

        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print(f"{column} not received by Trade")
                error = True
        if error:
            print(json.dumps(content))
            return jsonify(False)

        # Your code here

        # 1. Check the signature
        payload = content['payload']
        platform = payload['platform']
        payload_text = json.dumps(content['payload'])

        sk = content['sig']
        pk = payload['sender_pk']

        check = False

        if platform == 'Algorand':
            check = algosdk.util.verify_bytes(payload_text.encode('utf-8'), sk, pk)
        elif platform == 'Ethereum':
            eth_encoded_msg = eth_account.messages.encode_defunct(text=payload_text)
            check = (eth_account.Account.recover_message(eth_encoded_msg, signature=hex(int(sk, 16))) == pk)

        # 2. Add the order to the table
        if check:
            new_order = {
                'signature': sk,
                'buy_amount': payload['buy_amount'],
                'sell_amount': payload['sell_amount'],
                'sender_pk': payload['sender_pk'],
                'receiver_pk': payload['receiver_pk'],
                'sell_currency': payload['sell_currency'],
                'buy_currency': payload['buy_currency'],
                'tx_id': payload['tx_id']
            }

            attributes = ['signature',
                          'buy_amount',
                          'sell_amount',
                          'sender_pk',
                          'receiver_pk',
                          'sell_currency',
                          'buy_currency',
                          'tx_id']

            order_to_insert = Order(**{attr: new_order[attr] for attr in attributes})
            g.session.add(order_to_insert)
            g.session.commit()

            # 3a. Check if the order is backed by a transaction equal to the sell_amount (this is new)
            transactions = []
            if check_back(order_to_insert):
                # 3b. Fill the order (as in Exchange Server II) if the order is valid
                fill_order(order_to_insert, transactions)
                # 4. Execute the transactions
                execute_txes(transactions)
        else:
            log_message(content['payload'])
            return jsonify(False)
    return jsonify(True)


@app.route('/order_book')
def order_book():
    # Your code here
    # Note that you can access the database session using g.session
    order_list = g.session.query(Order).all()
    return jsonify({'data': [{'sender_pk': order.sender_pk,
                              'receiver_pk': order.receiver_pk,
                              'buy_currency': order.buy_currency,
                              'sell_currency': order.sell_currency,
                              'buy_amount': order.buy_amount,
                              'sell_amount': order.sell_amount,
                              'signature': order.signature,
                              "tx_id": order.tx_id} for order in order_list]})


if __name__ == '__main__':
    # algo_sk, algo_pk = algosdk.account.generate_account();
    # print(algo_pk)
    # print(algo_sk)
    #
    # w3 = Web3()
    # w3.eth.account.enable_unaudited_hdwallet_features()
    # acct, mnemonic_secret = w3.eth.account.create_with_mnemonic()
    #
    # print(mnemonic_secret)
    # eth_pk = acct._address
    # eth_sk = acct._private_key
    # print(eth_pk)
    # print(eth_sk)
    app.run(port='5002')
