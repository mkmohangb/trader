from celery import shared_task
from celery import Task


@shared_task(ignore_result=False)
def submit():
