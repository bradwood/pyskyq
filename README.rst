.. image:: https://gitlab.com/bradwood/pyskyq/badges/master/pipeline.svg
   :target: https://gitlab.com/bradwood/pyskyq/pipelines

.. image:: https://badge.fury.io/py/pyskyq.svg
    :target: https://badge.fury.io/py/pyskyq

.. image:: https://img.shields.io/readthedocs/pip.svg
   :target: https://pyskyq.readthedocs.io/en/latest/


======
pyskyq
======


A Python library for controlling a SkyQ Box.


Installing
==========

To install:

.. code:: bash

    pip install pyskyq


Using the cli
=============

You can use the cli tool like this:

.. code:: bash

    pyskyq play

This will press the "play" button on your Sky Q Remote. See constants.py_ for a list of the commands that can be passed.

.. _constants.py: https://gitlab.com/bradwood/pyskyq/blob/master/src/pyskyq/constants.py


Using the library
=================

The below snippet gives an example of usage:

.. code:: python

    from pyskyq import SkyQ

    skyq = SkyQ('1.2.3.4')
    skyq.remote.send_command(RCMD.play) # press play on the remote
    print(skyq.epg.get_channel(2002).desc) # print the description of of channel with sid=2002


Documentation
=============

Please refer to the documentation at pyskyq.readthedocs.io_.

.. _pyskyq.readthedocs.io: https://pyskyq.readthedocs.io/en/latest/


Contributions
=============

Contributions are welcome. Please fork the project on GitLab_ **Not GitHub** and raise an issue and
merge request there.

.. _GitLab: https://gitlab.com/bradwood/pyskyq/


Credits
=======
Code and ideas obtained from:

- https://github.com/dalhundal/sky-remote
- https://gladdy.uk/blog/2017/03/13/skyq-upnp-rest-and-websocket-api-interfaces/

Thank you to those individuals for their contributions.
