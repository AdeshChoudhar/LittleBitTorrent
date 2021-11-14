import os
import math
import hashlib
import threading

from helpers import *

if __name__ == "__main__":
    torrent_file_name = "torrents/ubuntu.torrent"
    file_data = read_decode_torrent_file(torrent_file_name)
    if file_data is None:
        exit(1)

    info, announce, optionals = dict(), "", dict()
    for i in file_data.keys():
        if i == b"info":
            info = file_data[i]
        elif i == b"announce":
            announce = file_data[i].decode()
        else:
            optionals[i] = file_data[i]

    piece_length, hash_pieces, name = 0, list(), ""
    for i in info.keys():
        if i == b"piece length":
            piece_length = info[i]
        elif i == b"pieces":
            pieces = info[i]
            for j in range(0, len(pieces), 20):
                hash_pieces.append({
                    "piece": pieces[j: j + 20],
                    "is_available": False
                })
        elif i == b"name":
            name = info[i].decode()

    is_multi_file_mode = b"files" in info.keys()
    file, files, total_length = "", list(), 0
    if not is_multi_file_mode:
        files = info[b"name"].decode()
        total_length = info[b"length"]
    else:
        for i in info[b"files"]:
            files.append({
                "length": i[b"length"],
                "path": os.path.join(*map(bytes.decode, i[b"path"]))
            })
            total_length += i[b"length"]
    total_pieces = math.ceil(total_length / piece_length)
    last_piece = total_length - piece_length * (total_pieces - 1)

    info_hash = hashlib.sha1(bencodepy.encode(info)).digest()
    peer_id = b'\x00\x00\x00\x00' + uuid.uuid4().bytes
    response = None
    if announce.startswith("http"):
        response = connect_with_http_tracker(announce, info_hash, peer_id, total_length)
    elif announce.startswith("udp"):
        response = connect_with_udp_tracker(announce, info_hash, peer_id, total_length)
    if response is None:
        exit(1)

    peers_fetch = fetch_peers(response)
    print(f"NUMBER OF PEERS FETCHED: {len(peers_fetch)}")

    pstrlen = int.to_bytes(19, 1, "big")
    pstr = "BitTorrent protocol".encode()
    reserved = "00000000".encode()
    handshake_message = pstrlen + pstr + reserved + info_hash + peer_id

    peer_handshake_threads = list()
    for peer in peers_fetch:
        thread = threading.Thread(
            target=handshake_with_peer,
            args=[peer, handshake_message]
        )
        peer_handshake_threads.append(thread)
        thread.setDaemon(True)
        thread.start()

    print("\nINITIATING HANDSHAKES...")
    for i in range(len(peer_handshake_threads)):
        peer_handshake_threads[i].join(5)
        progress_bar(i + 1, len(peer_handshake_threads))

    peers_handshake = list()
    for peer in peers_fetch:
        if peer.__contains__("handshake"):
            peers_handshake.append(peer)
    print(f"\nSUCCESSFUL HANDSHAKES: {len(peers_handshake)}")

    for peer in peers_handshake:
        parse_handshake_message(peer)
