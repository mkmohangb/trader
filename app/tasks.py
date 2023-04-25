from celery import shared_task, chain
from celery.signals import worker_ready
from . import storage as sg
from . import ticker
from threading import Event


@worker_ready.connect
def at_start(sender, **kwargs):
    print("in at_start method")
    print("after start_ticker")


@shared_task(ignore_result=False)
def add(a: int, b: int) -> int:
    print("number of records is ", sg.trades.count_documents({}))
    return a + b

def _print_strike(ce, pe, e):
    print(f"Strike is {ce}, {pe}")
    e.set()

@shared_task(ignore_result=False)
def monitor_skew(order_info):
    e = Event()
    ws = ticker.start_ticker(lambda ce,pe: _print_strike(ce, pe, e))
    e.wait()
    #ws.close()
    print("monitoring skew success")
    return "complete"


@shared_task(ignore_result=False)
def initiate_trade(order_info):
    print("received trade request: ", order_info.values())
    return "sucess"
    # monitor skew
    # place order
    # monitor if CSL
