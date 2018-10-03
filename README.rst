.. image:: https://gitlab.com/bradwood/pyskyq/badges/master/pipeline.svg
   :target: https://gitlab.com/bradwood/pyskyq/pipelines

.. image:: https://badge.fury.io/py/pyskyq.svg
    :target: https://badge.fury.io/py/pyskyq

.. image:: https://readthedocs.org/projects/pyskyq/badge/?version=latest
    :target: https://pyskyq.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


======
pyskyq
======


A Python library for controlling a SkyQ Box.


Installing
==========

To install:

.. code:: bash

    pip install pyskyq


Usage
=====

There are currently three main capabilities provided by the library.

Pressing buttons on the remote
------------------------------

Here is how to emulate a button-press on the SkyQ Remote. See :class:`~pyskyq.constants.RCMD` for
the various buttons that can be pressed.

.. code:: python

    from pyskyq import Remote, RCMD

        press_remote('skyq', getattr(RCMD, pargs.cmd))

Logging and reacting to status changes on the box
-------------------------------------------------

Here is how to set up an event listener that can be polled for box status changes.

.. code:: python

    from pyskyq import Status


    stat = Status('1.2.3.4')  # replace with hostname / IP of your Sky box
    stat.create_event_listener()  # set up listener thread.

    # do other stuff.

    # standby property will be updated asynchronously when the box is turned on or off.
    if stat.standby:
        print('The SkyQ Box is in Standby Mode')
    else:
        print('The SkyQ Box is in Online Mode')

    stat.shudown_event_listener()  # shut down listener thread.


Loading and interrogating channel data
--------------------------------------

Getting access to channel data requires initialising an :class:`~pyskyq.epg.EPG` object. Once
this is done, you need to load the channel data from the box using :meth:`pyskyq.epg.EPG.load_channel_data()`.

To access this data use :meth:`pyskyq.epg.EPG.get_channel()`. See the method's documentation for the
full list of available attributes.

.. code:: python

    from pyskyq import EPG

    epg = EPG(('1.2.3.4')  # replace with hostname / IP of your Sky box
    epg.load_channel_data() # load channel listing from Box.
    print(epg.get_channel(2002).desc) # print out the description of channel with sid = 2002


Documentation
=============

Please refer to the documentation at https://pyskyq.readthedocs.io/.


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
