import asyncio
from asyncio.exceptions import LimitOverrunError, IncompleteReadError
import time

from config import PEER_ID, PSTRLEN, PSTR, RESERVED
from util import throw_error


class Peer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.am_interested = False
        self.peer_choking = True
        self.handshake = bytes()
        self.rate = 0

    async def get_handshake(self, info_hash):
        handshake_request = PSTRLEN + PSTR + RESERVED + info_hash + PEER_ID
        try:
            reader, writer = await asyncio.open_connection(self.ip, self.port)
            writer.write(handshake_request)
            await writer.drain()
            start_time = time.time()
            handshake_response = await reader.read(65536)
            end_time = time.time()
            duration = end_time - start_time
            if handshake_response != bytes():
                received_info_hash = handshake_response[28:48]
                if received_info_hash != info_hash:
                    throw_error("INFO HASH MISMATCH!")
        except (OSError, LimitOverrunError, IncompleteReadError):
            raise Exception("PEER HANDSHAKE FAILED!")
        else:
            self.handshake = handshake_response
            self.rate = len(handshake_response) / duration
            writer.close()
            await writer.wait_closed()
