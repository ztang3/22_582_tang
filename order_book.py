from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from models import Base, Order

engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def process_order(order):
    order = Order(buy_currency=order['buy_currency'],
                  sell_currency=order['sell_currency'],
                  buy_amount=order['buy_amount'],
                  sell_amount=order['sell_amount'],
                  sender_pk=order['sender_pk'],
                  receiver_pk=order['receiver_pk'])

    session.add(order)

    db_rate = Order.sell_amount / Order.buy_amount
    ord_rate = order.buy_amount / order.sell_amount

    results = session.query(Order).filter(Order.filled == order.filled,
                                          Order.sell_currency == order.buy_currency,
                                          Order.buy_currency == order.sell_currency,
                                          db_rate >= ord_rate).first()

    if results:
        order.filled = datetime.now()
        order.counterparty_id = results.id

        results.filled = datetime.now()
        results.counterparty_id = order.id

        if order.buy_amount != results.sell_amount:
            if order.buy_amount - results.sell_amount < 0:
                b = Order(buy_currency=results.buy_currency,
                          sell_currency=results.sell_currency,
                          sender_pk=results.sender_pk,
                          receiver_pk=results.receiver_pk,
                          buy_amount=(results.sell_amount - order.buy_amount) / (
                                      results.sell_amount / results.buy_amount),
                          sell_amount=results.sell_amount - order.buy_amount,
                          creator_id=results.id)
            else:
                b = Order(buy_currency=order.buy_currency,
                          sell_currency=order.sell_currency,
                          sender_pk=order.sender_pk,
                          receiver_pk=order.receiver_pk,
                          buy_amount=order.buy_amount - results.sell_amount,
                          sell_amount=(order.buy_amount - results.sell_amount) / (
                                  order.buy_amount / order.sell_amount),
                          creator_id=order.id)

            session.add(b)
        session.commit()
        session.close()
