from celery import shared_task
from celery.signals import worker_ready
from . import storage as sg
from . import ticker


@worker_ready.connect
def at_start(sender, **kwargs):
    print("in at_start method")
    ticker.start_ticker()
    print("after start_ticker")


@shared_task(ignore_result=False)
def add(a: int, b: int) -> int:
    print("number of records is ", sg.trades.count_documents({}))
    return a + b
