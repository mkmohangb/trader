from celery import shared_task, chain
from celery.signals import worker_ready
from . import storage as sg
from . import ticker
from threading import Event
from kiteconnect import KiteConnect
import os
from bson.objectid import ObjectId


@worker_ready.connect
def at_start(sender, **kwargs):
    print("in at_start method")
    print("after start_ticker")


@shared_task(ignore_result=False)
def add(a: int, b: int) -> int:
    print("number of records is ", sg.trades.count_documents({}))
    return a + b


def _set_strike(trades, orders, e):
    print(f"Strike is {trades[0]['tradingsymbol']}, {trades[1]['tradingsymbol']}")
    if orders is not None:
        orders.extend(trades)
    e.set()


@shared_task(ignore_result=False)
def monitor_skew(order_info):
    sg.trades.update_one({"_id": ObjectId(order_info["_id"])},
                         {"$set": {"status": "monitoring skew"}})
    e = Event()
    orders = []
    ws = ticker.start_ticker(lambda trades: _set_strike(trades, orders, e))
    e.wait()
    ws.close()
    print("monitoring skew success")
    return orders


@shared_task(ignore_result=False)
def place_order(trades, order_info):
    print("in place order ", trades)
    sg.trades.update_one({"_id": ObjectId(order_info["_id"])},
                         {"$set": {"status": "place_order"}})
    return trades
#    try:
#        kite = KiteConnect(api_key=os.environ["kite_api_key"],
#                           access_token=os.environ["kite_access_token"])
#        ce_order_id = kite.place_order(variety="regular",
#                                          exchange="NFO",
#                                          tradingsymbol=trades[0]["tradingsymbol"],
#                                          transaction_type="SELL",
#                                          quantity=50,
#                                          order_type="MARKET",
#                                          product="MIS")
#        print("ce order id is ", ce_order_id)
#        pe_order_id = kite.place_order(variety="regular",
#                                          exchange="NFO",
#                                          tradingsymbol=trades[1]["tradingsymbol"],
#                                          transaction_type="SELL",
#                                          quantity=50,
#                                          order_type="MARKET",
#                                          product="MIS")
#        print("pe order id is ", pe_order_id)
#    except Exception as e:
#        print("order placement failed:", e)


@shared_task(ignore_result=False)
def monitor_premium(trades, order_info):
    print(f"premium is {trades}, stoploss is {order_info}")
    sg.trades.update_one({"_id": ObjectId(order_info["_id"])},
                         {"$set": {"status": "monitor_premium"}})
    e = Event()
    ws = ticker.start_ticker(lambda trades: _set_strike(trades, None, e), 5)
    e.wait()
    ws.close()
    print("combined Stop loss hit")
    return "completed"


@shared_task(ignore_result=False)
def initiate_trade(order_info):
    print("received trade request: ", order_info.values())
    res = (monitor_skew.s(order_info) | place_order.s(order_info) |
           monitor_premium.s(order_info))()
    print("res is ", res, type(res))
    return res
