
======
pyskyq
======

|Build Status| |docs| |pypi| |python| |license|

A Python library for controlling a SkyQ Box.

Introduction
============

This library aims to eventually provide API access to the `Sky Q Set Top Box`_.  It
is only tested on Python 3.7 and uses the newer async support offered by this version
of Python.

It uses the **excellent** trio_ async library and so knowledge of this is advised.

It is still a work in progress, but what is here, works.


.. _Sky Q Set Top Box: https://www.sky.com/shop/tv/sky-q/
.. _trio: https://trio.readthedocs.io/en/latest/


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

Here is how to emulate a button-press on the SkyQ Remote. See the documentation
for the class `REMOTECOMMANDS` for the various buttons that can be pressed.

.. code:: python

    from pyskyq import Remote, RCMD

        press_remote('skyq', RCMD.play)

Reacting to status changes on the box
-------------------------------------

Here is how to set up an async context manager that can be used to react to
changed events on the box..

.. code:: python

    from pyskyq import get_status

    async def report_box_online():
        """Report whether the SkyQ is online or not."""
        # pylint: disable=not-async-context-manager
        async with get_status('skyq') as stat:
            while True:
                if stat.online:
                    print('The SkyQ Box is Online ')
                else:
                    print('The SkyQ Box is Offline')
                await trio.sleep(1)
    try:
        print("Type Ctrl-C to exit.")
        trio.run(report_box_online)
    except KeyboardInterrupt:
        raise SystemExit(0)


Loading and interrogating channel data
--------------------------------------

Getting access to channel data requires initialising an ``EPG`` object. Once
this is done, you need to load the channel data from the box using the
``EPG.load_skyq_channel_data()`` method.

To access this data use ``EPG.get_channel()``. See the method's documentation
for the full list of available attributes.

.. code:: python

    from pyskyq import EPG

    async def main():
        """Run main routine, allowing arguments to be passed."""
        pargs = parse_args(args)
        epg = EPG('skyq')  # replace with hostname / IP of your Sky box
        await epg.load_skyq_channel_data()  # load channel listing from Box.
        all_72_hour = XMLTVListing('http://www.xmltv.co.uk/feed/6715')

        async with trio.open_nursery() as nursery:
            nursery.start_soon(all_72_hour.fetch)

        epg.apply_XMLTVListing(all_72_hour)

        print('Channel Description from the SkyQ Box:')
        print(epg.get_channel_by_sid(2002).desc)
        print('Channel XMLTV ID from the XMLTV Feed:')
        print(epg.get_channel_by_sid(2002).xmltv_id)
        print('Channel Logo URL from the XMLTV Feed:')
        print(epg.get_channel_by_sid(2002).xmltv_icon_url)

    if __name__ == "__main__":
        trio.run(main)


Documentation
=============

Please refer to the documentation at https://bradwood.gitlab.io/pyskyq/html/


Contributions
=============

Contributions are welcome. Please fork the project on GitLab_ **Not GitHub** and
raise an issue and merge request there.

.. _GitLab: https://gitlab.com/bradwood/pyskyq/


Credits
=======
Code and ideas obtained from:

- https://github.com/dalhundal/sky-remote
- https://gladdy.uk/blog/2017/03/13/skyq-upnp-rest-and-websocket-api-interfaces/

Thank you to those individuals for their contributions.



.. |Build Status| image:: https://gitlab.com/bradwood/pyskyq/badges/master/pipeline.svg
   :target: https://gitlab.com/bradwood/pyskyq/pipelines

.. |docs| image:: https://img.shields.io/badge/docs-passing-brightgreen.svg
   :target: https://bradwood.gitlab.io/pyskyq/html/

.. |pypi| image:: https://badge.fury.io/py/pyskyq.svg
   :target: https://badge.fury.io/py/pyskyq

.. |python| image:: https://img.shields.io/pypi/pyversions/pyskyq.svg
   :target: https://pypi.org/project/pyskyq/

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://gitlab.com/bradwood/pyskyq/raw/master/LICENSE.txt

