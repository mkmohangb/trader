from celery import shared_task
from celery.signals import worker_ready
from . import storage as sg
from . import ticker


@worker_ready.connect
def at_start(sender, **kwargs):
    print("in at_start method")
    #ticker.start_ticker()
    print("after start_ticker")


@shared_task(ignore_result=False)
def add(a: int, b: int) -> int:
    print("number of records is ", sg.trades.count_documents({}))
    return a + b


@shared_task(ignore_result=False)
def initiate_trade(order_info):
    print("received trade request: ", order_info.values())
    return "sucess"
    # monitor skew
    # place order
    # monitor if CSL
