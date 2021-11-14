import socket
import bencodepy
import requests
import uuid


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


def connect_with_http_tracker(announce, info_hash, peer_id, left):
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
                "compact": 1,
                "event": "started",
            }
        )
        response = bencodepy.decode(response.content)
        print("CONNECTED WITH THE TRACKER SUCCESSFULLY!")
    except requests.exceptions.RequestException:
        print("ERROR: CONNECTION WITH THE TRACKER FAILED!")
    return response


def connect_with_udp_tracker(announce, info_hash, peer_id, left):
    response = None
    try:
        connection_id = int("41727101980", 16).to_bytes(8, "big")
        action = int.to_bytes(0, 4, "big")
        transaction_id = int.to_bytes(uuid.uuid4().int % 2 ** 32, 4, "big")
        connection_message = connection_id + action + transaction_id
        tracker_url = announce[6:].split(":")[0]
        tracker_port = int(announce[6:].split(":")[1].split("/")[0])
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as tracker_socket:
            tracker_socket.sendto(connection_message, (tracker_url, tracker_port))
            connection_response, address = tracker_socket.recvfrom(65536)
            received_action = int.from_bytes(connection_response[:4], "big")
            received_transaction_id = connection_response[4:8]
            received_connection_id = connection_response[8:16]
            if (received_action == 0) and (received_transaction_id == transaction_id):
                action = int.to_bytes(1, 4, "big")
                transaction_id = int.to_bytes(uuid.uuid4().int % 2 ** 32, 4, "big")
                downloaded = int.to_bytes(0, 8, "big")
                left = left.to_bytes(8, "big")
                uploaded = int.to_bytes(0, 8, "big")
                event = int.to_bytes(0, 4, "big")
                ip = int.to_bytes(0, 4, "big")
                key = int.to_bytes(uuid.uuid4().int % 2 ** 32, 4, "big")
                num_want = int.to_bytes(-1, 4, "big", signed=True)
                port = int.to_bytes(6889, 2, "big")
                announce_message = received_connection_id + action + transaction_id + info_hash + peer_id + downloaded + left + uploaded + event + ip + key + num_want + port
                tracker_socket.sendto(announce_message, (tracker_url, tracker_port))
                announce_response, address = tracker_socket.recvfrom(65535)
                received_action = int.from_bytes(announce_response[:4], "big")
                received_transaction_id = announce_response[4:8]
                if (received_action == 1) and (received_transaction_id == transaction_id):
                    response = {
                        b"interval": int.from_bytes(announce_response[8:12], "big"),
                        b"incomplete": int.from_bytes(announce_response[12:16], "big"),
                        b"complete": int.from_bytes(announce_response[16:20], "big"),
                        b"peers": announce_response[20:]
                    }
                    print("CONNECTED WITH THE TRACKER SUCCESSFULLY!")
                else:
                    raise ConnectionError
            else:
                raise ConnectionError
    except ConnectionError:
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
    print(f"[{bar}] {percentage}% {count}/{total}\r", end="")


def handshake_with_peer(peer, handshake_message):
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
                    peer["handshake"] = received_handshake[pstrlen + 49:]
        except OSError:
            pass


def parse_handshake_message(peer):
    index = 0
    handshake = peer["handshake"]
    message_length = int.from_bytes(handshake[index:index + 4], "big")
    if message_length:
        message_id = int.from_bytes(handshake[index + 4: index + 5], "big")
        message = handshake[index + 5:]
        if message_id == 20:
            index += (4 + message_length)
            message_id = int.from_bytes(handshake[index + 4:index + 5], "big")
            message = handshake[index + 5:]
        if message_id == 5:
            peer["bitfield"] = message
