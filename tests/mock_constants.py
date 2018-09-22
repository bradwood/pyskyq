SERVICE_SUMMARY_MOCK = {
    "documentId": "683",
    "services": [
        {
            "c": "101",
            "dvbtriplet": "2.2045.6301",
            "schedule": True,
            "servicetype": "DSAT",
            "sf": "sd",
            "sg": 12,
            "sid": "2002",
            "sk": 2002,
            "t": "BBC One Lon",
            "xsg": 3
        },
        {
            "c": "0214",
            "dvbtriplet": "2.2095.55128",
            "servicetype": "DSAT",
            "sf": "au",
            "sg": 20,
            "sid": "2862",
            "sk": 2862,
            "t": "UCB Ireland",
            "xsg": 4
        }
    ],
    "version": 3
}

SERVICE_DETAIL_1 = {
    "details": {
        "dvbtriplet": "2.2045.6301",
        "isbroadcasting": True,
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

SERVICE_DETAIL_2 = {
    "details": {
        "dvbtriplet": "2.2095.55128",
        "isbroadcasting": True,
        "upgradeMessage": "A channel for God's Peace."
    },
    "sid": "2862",
    "streamingprofiles": [
        {
            "name": "AnExample",
            "suri": "http://10.0.1.6:4730/trans_caption/CHAN%3Alocator%3A5%3A3%3AB2E/profileAnExample.ttml",
            "uri": "http://10.0.1.6:4730/trans/CHAN%3Alocator%3A5%3A3%3AB2E/profileAnExample.ts"
        }
    ]
}

SERVICE_MOCK = [SERVICE_SUMMARY_MOCK,SERVICE_DETAIL_1,SERVICE_DETAIL_2]

REMOTE_TCP_MOCK = [  # set up the data to be returned on each successive call of socket.recv()
    b'SKY 000.001\n',
    b'\x01\x01',
    b'\x00\x00\x00\x00',
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
]
