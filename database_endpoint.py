from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine, select, MetaData, Table
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only

from models import Base, Order, Log

engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)


# These decorators allow you to use g.session to access the database inside the request code
@app.before_request
def create_session():
    g.session = scoped_session(
        DBSession)  # g is an "application global" https://flask.palletsprojects.com/en/1.1.x/api/#application-globals


@app.teardown_appcontext
def shutdown_session(response_or_exc):
    g.session.commit()
    g.session.remove()


"""
-------- Helper methods (feel free to add your own!) -------
"""


def log_message(d):
    # Takes input dictionary d and writes it to the Log table
    payload = d['payload']
    log = Log(message=json.dumps(payload))
    return log


"""
---------------- Endpoints ----------------
"""


@app.route('/trade', methods=['POST'])
def trade():
    if request.method == "POST":
        content = request.get_json(silent=True)
        print(f"content = {json.dumps(content)}")
        columns = ["sender_pk", "receiver_pk", "buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform"]
        fields = ["sig", "payload"]
        error = False
        for field in fields:
            if not field in content.keys():
                print(f"{field} not received by Trade")
                print(json.dumps(content))
                log_message(content)
                return jsonify(False)

        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print(f"{column} not received by Trade")
                error = True
        if error:
            print(json.dumps(content))
            log_message(content)
            return jsonify(False)

        # Your code here
        # Note that you can access the database session using g.session
        check = False
        payload = content['payload']
        payload_text = json.dumps(payload)

        platform = payload['platform']

        sk = content['sig']
        pk = payload['sender_pk']

        if platform == 'Algorand':
            check = algosdk.util.verify_bytes(payload_text.encode('utf-8'), sk, pk)
        elif platform == 'Ethereum':
            return_pk = eth_account.Account.recover_message(eth_account.messages.encode_defunct(text=payload_text),
                                                            signature=sk)
            if pk == return_pk:
                check = True

        if check:
            order = Order(
                signature=sk,
                sender_pk=pk,
                receiver_pk=payload['receiver_pk'],
                buy_currency=payload['buy_currency'],
                sell_currency=payload['sell_currency'],
                buy_amount=payload['buy_amount'],
                sell_amount=payload['sell_amount']
            )
            g.session.add(order)
            g.session.commit()
        else:
            log_message(content)

        return jsonify(check)


@app.route('/order_book')
def order_book():
    # Your code here
    # Note that you can access the database session using g.session
    orders = g.session.query(Order).all()
    result = {'data':
                  [{'sender_pk': o.sender_pk,
                    'receiver_pk': o.receiver_pk,
                    'buy_currency': o.buy_currency,
                    'sell_currency': o.sell_currency,
                    'buy_amount': o.buy_amount,
                    'sell_amount': o.sell_amount,
                    'signature': o.signature} for o in orders]
              }

    return jsonify(result)


if __name__ == '__main__':
    app.run(port='5002')
