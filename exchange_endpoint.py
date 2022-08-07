from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only
from datetime import datetime
import sys

from models import Base, Order, Log

engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)


@app.before_request
def create_session():
    g.session = scoped_session(DBSession)


@app.teardown_appcontext
def shutdown_session(response_or_exc):
    sys.stdout.flush()
    g.session.commit()
    g.session.remove()


""" Suggested helper methods """


def check_sig(payload, sig):
    platform = payload['platform']
    sender_pk = payload['sender_pk']
    payload_str = json.dumps(payload)

    is_verified = False

    if platform == 'Algorand':
        is_verified = algosdk.util.verify_bytes(payload_str.encode('utf-8'), sig, sender_pk)
    elif platform == 'Ethereum':
        is_verified = eth_account.Account.recover_message(eth_account.messages.encode_defunct(text=payload_str),
                                                          signature=sig) == sender_pk

    return is_verified


def fill_order(order):
    g.session.add(order)
    g.session.commit()

    result = g.session.query(Order).filter(Order.filled == None,
                                           Order.buy_currency == order.sell_currency,
                                           Order.sell_currency == order.buy_currency,
                                           (Order.sell_amount / Order.buy_amount) >= (
                                                   order.buy_amount / order.sell_amount),
                                           order.buy_amount != order.sell_amount,
                                           Order.sell_amount != Order.buy_amount
                                           ).first()

    if result is not None:
        if blance_check(order, result) is not None:
            fill_order(result)
    else:
        return


def blance_check(order, result):
    order.filled = datetime.now()
    result.filled = datetime.now()

    order.counterparty_id = result.id
    result.counterparty_id = order.id

    if order.buy_amount < result.sell_amount:
        ord_tmp = Order(creator_id=result.id,
                        sender_pk=result.sender_pk,
                        receiver_pk=result.receiver_pk,
                        buy_currency=result.buy_currency,
                        sell_currency=result.sell_currency,
                        buy_amount=(result.sell_amount - order.buy_amount) / (result.sell_amount / result.buy_amount),
                        sell_amount=(result.sell_amount - order.buy_amount))
        g.session.add(ord_tmp)
        g.session.commit()

    elif order.buy_amount > result.sell_amount:

        ord_tmp = Order(creator_id=order.id, sender_pk=order.sender_pk,
                        receiver_pk=order.receiver_pk,
                        buy_currency=order.buy_currency,
                        sell_currency=order.sell_currency, buy_amount=order.buy_amount - result.sell_amount,
                        sell_amount=(order.buy_amount - result.sell_amount) / (order.buy_amount / order.sell_amount))
        g.session.add(ord_tmp)
        g.session.commit()

    else:
        g.session.commit()


def log_message(d):
    log_info = Log(message=json.dumps(d), logtime=datetime.now())
    g.session.add(log_info)
    g.session.commit()


""" End of helper methods """


@app.route('/trade', methods=['POST'])
def trade():
    print("In trade endpoint")
    if request.method == "POST":
        content = request.get_json(silent=True)
        print(f"content = {json.dumps(content)}")
        columns = ["sender_pk", "receiver_pk", "buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform"]
        fields = ["sig", "payload"]

        for field in fields:
            if not field in content.keys():
                print(f"{field} not received by Trade")
                print(json.dumps(content))
                log_message(content)
                return jsonify(False)

        for column in columns:
            if not column in content['payload'].keys():
                print(f"{column} not received by Trade")
                print(json.dumps(content))
                log_message(content)
                return jsonify(False)

        # Your code here
        # Note that you can access the database session using g.session

        # TODO: Check the signature
        payload = content['payload']
        secret_k = content['sig']

        is_verified = check_sig(payload, secret_k)

        # TODO: Add the order to the database
        # TODO: Fill the order
        new_ord = Order(sender_pk=payload['sender_pk'],
                        receiver_pk=payload['receiver_pk'],
                        buy_currency=payload['buy_currency'],
                        sell_currency=payload['sell_currency'],
                        buy_amount=payload['buy_amount'],
                        sell_amount=payload['sell_amount'],
                        signature=secret_k)

        if is_verified:
            fill_order(new_ord)
        else:
            log_message(content)

        # TODO: Be sure to return jsonify(True) or jsonify(False) depending on if the method was successful

        return jsonify(is_verified)


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
                              'signature': order.signature} for order in order_list]})


if __name__ == '__main__':
    app.run(port='5002')
