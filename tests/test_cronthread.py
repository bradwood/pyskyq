import asyncio
import logging
import sys
import time

import pytest

import aiocron
from pyskyq import CronThread

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

def test_cronthread(capsys):
    t = CronThread()

    def spam():
        print('It works')


    t.crontab("* * * * * *",
              func=spam,
              start=True
              )

    time.sleep(3)
    t.stop()

    captured = capsys.readouterr()
    assert captured.out == "It works\nIt works\n"
