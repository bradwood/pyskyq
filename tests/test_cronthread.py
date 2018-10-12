import pytest
import aiocron
import asyncio
import time
from pyskyq.cronthread import CronThread

def test_cronthread(capsys):
    t = CronThread()

    def spam():
        print('It works')


    t.crontab("* * * * * *",
              func=spam,
              start=True
              )

    time.sleep(5)
    t.stop()

    captured = capsys.readouterr()
    assert captured.out == "It works\nIt works\nIt works\nIt works\n"
