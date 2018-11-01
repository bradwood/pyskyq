
SERVICE_SUMMARY_MOCK = """
{
    "documentId": "683",
    "services": [
        {
            "c": "101",
            "dvbtriplet": "2.2045.6301",
            "schedule": "true",
            "servicetype": "DSAT",
            "sf": "sd",
            "sg": 12,
            "sid": "2002",
            "sk": 2002,
            "t": "BBC One Lon",
            "xsg": 3
        },
        {
            "c" : "811",
            "dvbtriplet" : "2.2022.6506",
            "schedule" : true,
            "servicetype" : "DSAT",
            "sf" : "sd",
            "sg" : 12,
            "sid" : "2306",
            "sk" : 2306,
            "t" : "Dave",
            "xsg" : 3
        }
    ],
    "version": 3
}
"""

SERVICE_DETAIL_1 = """
{
    "details": {
        "dvbtriplet": "2.2045.6301",
        "isbroadcasting": true,
        "upgradeMessage": "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england."
    },
    "sid": "2002",
    "streamingprofiles": [
        {
            "name": "AnExample",
            "suri": "http://10.0.1.6:4730/trans_caption/CHAN%3Alocator%3A5%3A3%3A7D2/profileAnExample.ttml",
            "uri": "http://10.0.1.6:4730/trans/CHAN%3Alocator%3A5%3A3%3A7D2/profileAnExample.ts"
        }
    ]
}
"""

SERVICE_DETAIL_2 = """
{
    "details": {
        "dvbtriplet": "2.2022.6506",
        "isbroadcasting": true,
        "upgradeMessage": "Dave is the home of witty banter with quizcoms, cars and comedies."
    },
    "sid": "2306",
    "streamingprofiles": [
        {
            "name": "AnExample",
            "suri": "http://10.0.1.6:4730/trans_caption/CHAN%3Alocator%3A5%3A3%3A902/profileAnExample.ttml",
            "uri": "http://10.0.1.6:4730/trans/CHAN%3Alocator%3A5%3A3%3A902/profileAnExample.ts"
        }
    ]
}
"""

REMOTE_TCP_MOCK = [  # set up the data to be returned on each successive call of socket.recv()
    b'SKY 000.001\n',
    b'\x01\x01',
    b'\x00\x00\x00\x00',
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
]


WS_STATUS_MOCK = """
{
   "camessage" : {
      "reason" : "no message",
      "state" : "unavailable"
   },
   "drmstatus" : {
      "state" : "available"
   },
   "entitlements" : [
      "ANALYTICS",
      "BIGBASIC",
      "ETHAN_APP_1",
      "HD",
      "PDL",
      "SKY_DRM_CE",
      "SKY_DRM_MR",
      "SKY_IPPV",
      "ULTRA+",
      "SKY+",
      "GATEWAYENABLER",
      "SIDELOAD"
   ],
   "epginfobits" : {
      "epginfobits" : "0xFDE5FFC0",
      "mask" : "0x5FFA003F",
      "state" : "available"
   },
   "gatewayservices" : {
      "state" : "available"
   },
   "hdmi" : {
      "2160p10bitCapable" : false,
      "authenticatedHDCP" : "NONE",
      "reason" : "HDMI output port is disabled",
      "sinkHDCP" : "NONE",
      "sinkHLG" : false,
      "sinkUHD" : false,
      "state" : "available",
      "uhdConfigured" : false
   },
   "network" : {
      "state" : "available"
   },
   "nssplayback" : {
      "state" : "available"
   },
   "pvr" : {
      "state" : "available"
   },
   "schedule" : {
      "lastdate" : "20181005",
      "state" : "available"
   },
   "servicelist" : {
      "state" : "available"
   },
   "smartcard" : {
      "active" : true,
      "bouquet" : "4101",
      "countryCode" : "GBR",
      "currency" : "GBP",
      "cwe" : true,
      "householdid" : "12345678",
      "paired" : true,
      "state" : "available",
      "subbouquet" : "1",
      "transactionlimit" : 65535,
      "viewingCardNumber" : "123 456 789"
   },
   "swupdate" : {
      "reason" : "IDLE",
      "state" : "unavailable"
   },
   "systemupdates" : {
      "entitlements" : 2,
      "install" : 1,
      "servicegenres" : 1,
      "smartcard" : 1
   },
   "updatetask" : {
      "reason" : "no update",
      "state" : "unavailable"
   }
}

"""

XML_CHANNEL_1 = """
  <channel id="f3932e75f691561adbe3b609369e487b">
    <display-name>BBC One Lon</display-name>
    <blah>Not understood, not processed, so should be ignored.</blah>
    <icon src="/images/channels/f3932e75f691561adbe3b609369e487b.png"/>
  </channel>
"""

XML_CHAN_JSON = """{
    "__type__": "__channel__",
    "attributes": {
        "sid": null,
        "c": null,
        "t": null,
        "xmltv_id": "f3932e75f691561adbe3b609369e487b",
        "xmltv_display_name": "BBC One Lon",
        "xmltv_icon_url": "http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png"
    },
    "sources": 4
}
"""

SKYQ_CHAN_JSON = """{
    "__type__": "__channel__",
    "attributes": {
        "sid": "2002",
        "c": "101",
        "t": "BBC One Lon",
        "xmltv_id": null,
        "dvbtriplet": "2.2045.6301",
        "schedule": "true",
        "servicetype": "DSAT",
        "sf": "sd",
        "sg": 12,
        "sk": 2002,
        "xsg": 3,
        "isbroadcasting": true,
        "upgradeMessage": "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england."
    },
    "sources": 3
}
"""

MERGED_CHAN_JSON = """{
    "__type__": "__channel__",
    "attributes": {
        "sid": "2002",
        "c": "101",
        "t": "BBC One Lon",
        "xmltv_id": "f3932e75f691561adbe3b609369e487b",
        "dvbtriplet": "2.2045.6301",
        "schedule": "true",
        "servicetype": "DSAT",
        "sf": "sd",
        "sg": 12,
        "sk": 2002,
        "xsg": 3,
        "isbroadcasting": true,
        "upgradeMessage": "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england.",
        "xmltv_display_name": "BBC One Lon",
        "xmltv_icon_url": "http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png"
    },
    "sources": 7
}
"""


BAD_JSON = """
{
    "attributes": {
        "sid": "2002",
        "c": "101",
        "t": "BBC One Lon",
        "xmltv_id": "f3932e75f691561adbe3b609369e487b",
        "dvbtriplet": "2.2045.6301",
        "schedule": "true",
        "servicetype": "DSAT",
        "sf": "sd",
        "sg": 12,
        "sk": 2002,
        "xsg": 3,
        "isbroadcasting": true,
        "upgradeMessage": "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england.",
        "xmltv_display_name": "BBC One Lon",
        "xmltv_icon_url": "http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png"
    },
    "sources": 7
}
"""
FUZZY_CHANNELS_MOCK = """
{
    "documentId": "683",
    "services": [
        {
            "c": "101",
            "dvbtriplet": "2.2045.6301",
            "schedule": "true",
            "servicetype": "DSAT",
            "sf": "sd",
            "sg": 12,
            "sid": "2002",
            "sk": 2002,
            "t": "BBC One Lon",
            "xsg": 3
        },
        {
            "c": "102",
            "dvbtriplet": "2.2045.6301",
            "schedule": "true",
            "servicetype": "DSAT",
            "sf": "hd",
            "sg": 12,
            "sid": "2002",
            "sk": 2002,
            "t": "BBC One Lon HD",
            "xsg": 3
        },
        {
            "c": "103",
            "dvbtriplet": "2.2045.6301",
            "schedule": "true",
            "servicetype": "DSAT",
            "sf": "hd",
            "sg": 12,
            "sid": "2002",
            "sk": 2002,
            "t": "BBC One HD",
            "xsg": 3
        },
        {
            "c": "104",
            "dvbtriplet": "2.2045.6301",
            "schedule": "true",
            "servicetype": "DSAT",
            "sf": "sd",
            "sg": 12,
            "sid": "2002",
            "sk": 2002,
            "t": "BBC One +1",
            "timeshifted": true,
            "xsg": 3
        },
        {
            "c": "105",
            "dvbtriplet": "2.2045.6301",
            "schedule": "true",
            "servicetype": "DSAT",
            "sf": "sd",
            "sg": 12,
            "sid": "2002",
            "sk": 2002,
            "t": "BBC News",
            "xsg": 3
        },
        {
            "c": "106",
            "dvbtriplet": "2.2045.6301",
            "schedule": "true",
            "servicetype": "DSAT",
            "sf": "sd",
            "sg": 12,
            "sid": "2002",
            "sk": 2002,
            "t": "BBC One YH",
            "xsg": 3
        },
        {
            "c": "107",
            "dvbtriplet": "2.2045.6301",
            "schedule": "true",
            "servicetype": "DSAT",
            "sf": "hd",
            "sg": 12,
            "sid": "2002",
            "sk": 2002,
            "t": "BBC One NI HD",
            "xsg": 3
        },
        {
            "c": "108",
            "dvbtriplet": "2.2045.6301",
            "schedule": "true",
            "servicetype": "DSAT",
            "sf": "sd",
            "sg": 12,
            "sid": "2002",
            "sk": 2002,
            "t": "BBC News Lon",
            "xsg": 3
        },
        {
            "c": "109",
            "dvbtriplet": "2.2045.6301",
            "schedule": "true",
            "servicetype": "DSAT",
            "sf": "hd",
            "sg": 12,
            "sid": "2002",
            "sk": 2002,
            "t": "BBC News HD",
            "xsg": 3
        },
        {
            "c" : "110",
            "dvbtriplet" : "2.2022.6506",
            "schedule" : true,
            "servicetype" : "DSAT",
            "sf" : "hd",
            "sg" : 12,
            "sid" : "2306",
            "sk" : 2306,
            "t" : "BBC News HD +1",
            "timeshifted": true,
            "xsg" : 3
        }
    ],
    "version": 3
}
"""
EPG_JSON = """
[
    {
        "__type__": "__channel__",
        "attributes": {
            "sid": "2002",
            "c": "101",
            "t": "BBC One Lon",
            "xmltv_id": null,
            "dvbtriplet": "2.2045.6301",
            "schedule": "true",
            "servicetype": "DSAT",
            "sf": "sd",
            "sg": 12,
            "sk": 2002,
            "xsg": 3,
            "isbroadcasting": true,
            "upgradeMessage": "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england."
        },
        "sources": 3
    },
    {
        "__type__": "__channel__",
        "attributes": {
            "sid": "2306",
            "c": "811",
            "t": "Dave",
            "xmltv_id": null,
            "dvbtriplet": "2.2022.6506",
            "schedule": true,
            "servicetype": "DSAT",
            "sf": "sd",
            "sg": 12,
            "sk": 2306,
            "xsg": 3,
            "isbroadcasting": true,
            "upgradeMessage": "Dave is the home of witty banter with quizcoms, cars and comedies."
        },
        "sources": 3
    },
    {
        "__type__": "__SOMETHING_TBC__",
        "attributes": {
            "blah": "yadda"
        }
    }
]
"""
