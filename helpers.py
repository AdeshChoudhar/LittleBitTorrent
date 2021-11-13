import socket
import bencodepy
import requests
import sys


def read_decode_torrent_file(torrent_file_name: str):
    file_data = None
    try:
        with open(torrent_file_name, "rb") as torrent_file:
            file_data = bencodepy.decode(torrent_file.read())
            print("FILE READ AND DECODED SUCCESSFULLY!")
    except FileNotFoundError:
        print("ERROR: FILE NOT FOUND!")
    except bencodepy.exceptions.BencodeDecodeError:
        print("ERROR: FILE CANNOT BE DECODED!")
    return file_data


def connect_with_tracker(announce: str, info_hash: bytes, peer_id: bytes, left: int):
    response = None
    try:
        response = requests.get(
            url=announce,
            params={
                "info_hash": info_hash,
                "peer_id": peer_id,
                "port": 6881,
                "uploaded": 0,
                "downloaded": 0,
                "left": left,
                "compact": 1
            }
        )
        response = bencodepy.decode(response.content)
        print("CONNECTED WITH THE TRACKER SUCCESSFULLY!")
    except requests.exceptions.RequestException:
        print("ERROR: CONNECTION WITH THE TRACKER FAILED!")
    return response


def fetch_peers(response: dict):
    peers = list()
    for i in range(0, len(response[b"peers"]), 6):
        peer = response[b"peers"][i:i + 6]
        peers.append({
            "ip": ".".join([str(j) for j in peer[:4]]),
            "port": int.from_bytes(peer[4:6], "big")
        })
    print("\nPEERS FETCHED SUCCESSFULLY!")
    return peers


def progress_bar(count, total):
    bar_length = 50
    bar_filled = round(bar_length * count / float(total))
    percentage = round(100.0 * count / float(total), 1)
    bar = f"{'=' * bar_filled}>{'-' * (bar_length - bar_filled - 1)}"
    print("[{}] {}% {}/{}\r".format(bar, percentage, count, total), end="")


def handshake_with_peer(peers: list, peer: dict, handshake_message: bytes):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as peer_socket:
        peer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            peer_socket.connect((peer["ip"], peer["port"]))
            peer_socket.send(handshake_message)
            received_handshake = bytes()
            while True:
                tmp = peer_socket.recv(65536)
                if not tmp:
                    break
                received_handshake += tmp
            if received_handshake:
                pstrlen = int.from_bytes(received_handshake[0:1], "big")
                info_hash = received_handshake[pstrlen + 9: pstrlen + 29]
                if info_hash == handshake_message[pstrlen + 9: pstrlen + 29]:
                    return
        except OSError:
            pass
        peers.remove(peer)
