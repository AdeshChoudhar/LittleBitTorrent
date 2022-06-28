from bencodepy import decode, encode
from bencodepy.exceptions import DecodingError
from os.path import join
from hashlib import sha1
from datetime import datetime
from math import ceil

from util import populate_dict, throw_error, format_size


class Torrent():
    def __init__(self, file):
        self.file = file
        self.data = self.get_data()
        self.info = self.get_info()
        self.pieces = self.get_pieces()
        self.files = self.get_files()
        self.trackers = self.get_trackers()
        self.webseeds = self.get_webseeds()
        self.info_hash = sha1(encode(self.data[b"info"])).digest()
        self.total_length = sum([file["length"] for file in self.files])
        self.piece_count = ceil(self.total_length / self.info[b'piece length'])

    def get_data(self):
        try:
            with open(self.file, "rb") as file:
                data = decode(file.read())
        except FileNotFoundError:
            throw_error(f"\"{self.file}\" could not be found")
        except DecodingError:
            throw_error(f"\"{self.file}\" could not be decoded")
        keys = [b"info", b"announce", b"announce-list", b"url-list",
                b"creation date", b"comment", b"created by", b"encoding"]
        return populate_dict(data, keys)

    def get_info(self):
        keys = [b"piece length", b"pieces", b"private", b"name"]
        if b"files" in self.data[b"info"]:
            keys += [b"files"]
        else:
            keys += [b"length", b"md5sum"]
        return populate_dict(self.data[b"info"], keys)

    def get_pieces(self):
        pieces = list()
        for i in range(0, len(self.info[b"pieces"]), 20):
            pieces.append({
                "piece": self.info[b"pieces"][i: i + 20],
                "is_available": False
            })
        return pieces

    def get_files(self):
        files = list()
        directory = self.info[b"name"].decode()
        if b"files" in self.info:
            for file in self.info[b"files"]:
                files.append({
                    "name": file[b"path"][-1].decode(),
                    "length": file[b"length"],
                    "md5sum": file[b"md5sum"] if b"md5sum" in file else None,
                    "path": join(directory, *map(bytes.decode, file[b"path"]))
                })
        else:
            files.append({
                "name": self.info[b"name"].decode(),
                "length": self.info[b"length"],
                "md5sum": self.info[b"md5sum"],
                "path": directory
            })
        return files

    def get_trackers(self):
        if self.data[b"announce-list"] is not None:
            trackers = self.data[b"announce-list"]
        else:
            trackers = [[self.data[b"announce"]]]
        return trackers

    def get_webseeds(self):
        webseeds = list()
        if self.data[b"url-list"] is not None:
            if type(self.data[b"url-list"]) is list:
                for url in list(map(bytes.decode, self.data[b"url-list"])):
                    if url.startswith("http") or url.startswith("ftp"):
                        webseeds.append(url)
            else:
                url = self.data[b"url-list"].decode()
                if url.startswith("http") or url.startswith("ftp"):
                    webseeds.append(url)
        return webseeds

    def show_metadata(self):
        print(f"Name: {self.info[b'name'].decode()}")
        print(f"File: {self.file}\n")

        print("GENERAL\n")

        print(f"  Name: {self.info[b'name'].decode()}")
        print(f"  Hash: {self.info_hash.hex()}")
        date = datetime.fromtimestamp(self.data[b'creation date'])
        print(f"  Created by: {self.data[b'created by'].decode()}")
        print(f"  Created on: {date.strftime('%a %b %-d %H:%M:%S %Y')}")
        print(f"  Comment: {self.data[b'comment'].decode()}")
        print(f"  Piece Count: {self.piece_count}")
        print(f"  Piece Size: {format_size(self.info[b'piece length'], True)}")
        print(f"  Total Size: {format_size(self.total_length)}")
        privacy = "Private" if self.info[b"private"] == 1 else "Public"
        print(f"  Privacy: {privacy} torrent\n")

        print("TRACKERS\n")
        for tier, trackers in enumerate(self.trackers):
            print(f"  Tier #{tier + 1}")
            for tracker in trackers:
                print(f"  {tracker.decode().strip()}")
            print()

        if self.webseeds:
            print("WEBSEEDS\n")
            for webseed in self.webseeds:
                print(f"  {webseed}")
            print()

        print("FILES\n")
        for file in self.files:
            print(f"  {file['path']} ({format_size(file['length'])})")
        print()
