"""This module implements an asyncio-based cron-related classes.

It is heavily based on (ie, copied from):
    https://github.com/gawel/aiocron

Credit to Gael Pasgrimaud for his work here.

"""
import asyncio
import threading
import time
import aiocron


class CronThread(threading.Thread):

    def __init__(self): # set up the thread
        super(CronThread, self).__init__()
        self.loop = None
        self.start()
        time.sleep(.1)

    def run(self): # the thread code itself.
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        self.loop.close()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.join()

    def crontab(self, *args, **kwargs):
        kwargs['loop'] = self.loop
        return aiocron.crontab(*args, **kwargs)

