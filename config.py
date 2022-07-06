from uuid import uuid4


PEER_ID = "-LB0000-".encode() + uuid4().bytes[4:]
KEY = uuid4().int % (2 ** 32)

PORT_NO = 6881
NUMWANT = -1
