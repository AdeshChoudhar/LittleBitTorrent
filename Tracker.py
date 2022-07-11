import asyncio
from uuid import uuid4
from requests import get
from requests import exceptions
from bencodepy import decode
import socket
from socket import AF_INET, SOCK_DGRAM

from Peer import Peer
from config import PEER_ID, PORT_NO, NUMWANT, KEY, PEER_ID
from util import throw_error


class Tracker:
    def __init__(self, torrent):
        self.torrent = torrent
        self.announce = self.get_announce()
        self.response = self.get_response()
        self.peers = self.get_peers()
        asyncio.run(self.do_handshakes(self.torrent.info_hash))

    def get_announce(self):
        # TODO: Multitracker Metadata Extension
        # URLs: http://bittorrent.org/beps/bep_0012.html
        return self.torrent.trackers[0][0].decode().strip()

    def get_response(self):
        if self.announce.startswith("http"):
            return self.get_http_response()
        else:
            return self.get_udp_response()

    def get_http_response(self):
        try:
            response = get(
                url=self.announce,
                params={
                    "info_hash": self.torrent.info_hash,
                    "peer_id": PEER_ID,
                    "port": PORT_NO,
                    "uploaded": 0,
                    "downloaded": 0,
                    "left": self.torrent.total_length,
                    "compact": 1,
                    "event": "started",
                    "ip": 0,
                    "numwant": NUMWANT,
                    "key": KEY,
                    "trackerid": ""
                }
            )
            response.raise_for_status()
        except (ConnectionError, exceptions.RequestException):
            throw_error("CONNECTION WITH THE TRACKER FAILED!")
        else:
            response = decode(response.content)
            return response

    def get_udp_response(self):
        # TODO: UDP Tracker Protocol for BitTorrent
        # URLs: http://bittorrent.org/beps/bep_0015.html
        try:
            with socket.socket(AF_INET, SOCK_DGRAM) as udp_socket:
                protocol_id = int("41727101980", 16).to_bytes(8, "big")
                action = int.to_bytes(0, 4, "big")
                transaction_id = int.to_bytes(
                    uuid4().int % (2 ** 32), 4, "big")
                connect_request = protocol_id + action + transaction_id
                tracker_url = self.announce[6:].split(":")[0]
                tracker_port = int(
                    self.announce[6:].split(":")[1].split("/")[0]
                )
                udp_socket.sendto(connect_request, (tracker_url, tracker_port))

                connect_response, address = udp_socket.recvfrom(65536)
                if (len(connect_response) < 16) or \
                        (connect_response[4:8] != transaction_id) or \
                        (int.from_bytes(connect_response[:4], "big") != 0):
                    raise ConnectionError
                connect_id = connect_response[8:16]

                action = int.to_bytes(1, 4, "big")
                transaction_id = int.to_bytes(uuid4().int % 2 ** 32, 4, "big")
                downloaded = int.to_bytes(0, 8, "big")
                left = self.torrent.total_length.to_bytes(8, "big")
                uploaded = int.to_bytes(0, 8, "big")
                event = int.to_bytes(0, 4, "big")
                ip = int.to_bytes(0, 4, "big")
                key = int.to_bytes(KEY, 4, "big")
                num_want = int.to_bytes(NUMWANT, 4, "big", signed=True)
                port = int.to_bytes(PORT_NO, 2, "big")
                announce_request = connect_id + action + transaction_id + \
                    self.torrent.info_hash + PEER_ID + downloaded + left + \
                    uploaded + event + ip + key + num_want + port
                udp_socket.sendto(announce_request, (tracker_url, tracker_port))

                announce_response, address = udp_socket.recvfrom(65536)
                if (len(announce_response) < 20) or \
                        (announce_response[4:8] != transaction_id) or \
                        (int.from_bytes(announce_response[:4], "big") != 1):
                    raise ConnectionError
                response = {
                    b"interval": int.from_bytes(
                        announce_response[8:12], "big"
                    ),
                    b"incomplete": int.from_bytes(
                        announce_response[12:16], "big"
                    ),
                    b"complete": int.from_bytes(
                        announce_response[16:20], "big"
                    ),
                    b"peers": announce_response[20:]
                }
        except ConnectionError:
            throw_error("CONNECTION WITH THE TRACKER FAILED!")
        else:
            return response

    def get_peers(self):
        peers = list()
        for i in range(0, len(self.response[b"peers"]), 6):
            peer = self.response[b"peers"][i:i + 6]
            ip = ".".join([str(j) for j in peer[:4]])
            port = int.from_bytes(peer[4:6], "big")
            peers.append(Peer(ip, port))
        return peers

    async def do_handshakes(self, info_hash):
        tasks = list()
        for peer in self.peers:
            tasks.append(asyncio.create_task(peer.get_handshake(info_hash)))
        try:
            await asyncio.gather(*tasks, return_exceptions=False)
        except Exception:
            pass
