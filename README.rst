.. image:: https://gitlab.com/bradwood/pyskyq/badges/develop/pipeline.svg
   :target: https://gitlab.com/bradwood/pyskyq/pipelines

.. image:: https://gitlab.com/bradwood/pyskyq/badges/develop/coverage.svg
   :target: https://bradwood.gitlab.io/pyskyq/develop/coverage/


======
pyskyq
======


A Python library for controlling a SkyQ Box

Installing
==========

To install:

::

    pip install pyskyq

Using the cli
=============

You can use the cli tool like this:

::

    pyskyq play

See constants.py_ for a list of the commands that can be passed.

.. _constants.py: : src/pyskyq/constants.py

Using the library
=================

The below snippet gives an example of usage:

::

    from pyskyq import SkyQ

    skyq = SkyQ('1.2.3.4')
    skyq.remote.send_command(rcmd.play)

Credits
=======
Code and ideas obtained from:

- https://github.com/dalhundal/sky-remote
- https://gladdy.uk/blog/2017/03/13/skyq-upnp-rest-and-websocket-api-interfaces/

Thank you to those individuals for their contributions.
