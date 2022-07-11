from uuid import uuid4


PEER_ID = "-LB0000-".encode() + uuid4().bytes[4:]
KEY = uuid4().int % (2 ** 32)
PSTRLEN = int.to_bytes(19, 1, "big")
PSTR = "BitTorrent protocol".encode()
RESERVED = "00000000".encode()

PORT_NO = 6881
NUMWANT = -1
