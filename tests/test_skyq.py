import pytest
import logging
from pyskyq.skyq import SkyQ
from pyskyq.constants import REMOTE_PORT


@pytest.mark.parametrize("host,port,logger", [
    ("hostname", 5900, None),
    ("hostname", 2342, logging.getLogger()),
])
def test_SkyQ_init(host, port, logger):
    skybox = SkyQ(host, port, logger)
    assert skybox.host == host
    assert skybox.remote_port == port
    assert isinstance(skybox.logger, logging.Logger)

