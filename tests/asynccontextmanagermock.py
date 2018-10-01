from asynctest import MagicMock

class AsyncContextManagerMock(MagicMock):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key in ('aenter_return', 'aexit_return'):
            setattr(self, key,  kwargs[key] if key in kwargs else MagicMock())

    async def __aenter__(self):
        return self.aenter_return

    async def __aexit__(self, *args):
        return self.aexit_return

    # Grabbed this hack from here
    # https: // github.com/aaugustin/websockets/issues/359
    # doesnt' seem to work though :(
    # def __await__(self):
    #     return self
    #     yield None
