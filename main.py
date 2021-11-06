import os
import bencodepy
import math

if __name__ == "__main__":
    torrent_file_name = "torrents/pokemon.torrent"
    with open(torrent_file_name, "rb") as torrent_file:
        try:
            file_data = bencodepy.decode(torrent_file.read())
            print("FILE READ AND DECODED SUCCESSFULLY!")
        except FileNotFoundError:
            print("ERROR: FILE NOT FOUND!")
            exit(1)
        except bencodepy.exceptions.BencodeDecodeError:
            print("ERROR: FILE CANNOT BE DECODED!")
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
    file, length = "", 0
    files, total_length = list(), 0
    if not is_multi_file_mode:
        files = info[b"name"].decode()
        length = info[b"length"]
    else:
        for i in info[b"files"]:
            files.append({
                "length": i[b"length"],
                "path": os.path.join(*map(bytes.decode, i[b"path"]))
            })
            total_length += i[b"length"]
    total_pieces = math.ceil(total_length / piece_length)
    last_piece = total_length - piece_length * (total_pieces - 1)
