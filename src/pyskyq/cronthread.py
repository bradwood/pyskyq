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
    """Implement a cronjob in a thread."""

    def __init__(self):  # set up the thread
        """Initialise the thread."""
        super(CronThread, self).__init__()
        self.loop = None
        self.start()
        time.sleep(.1)

    def run(self): # the thread code itself.
        """Get an event loop and start it up in this thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        self.loop.close()

    def stop(self):
        """Stop the loop and join the thread."""
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.join()

    def crontab(self, *args, **kwargs):
        """Return an aiocron.contab object running in this loop."""
        kwargs['loop'] = self.loop
        return aiocron.crontab(*args, **kwargs)
