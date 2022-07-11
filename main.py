from sys import exit

from Torrent import Torrent
from Tracker import Tracker
from util import parse_arguments


if __name__ == "__main__":
    args = parse_arguments()

    torrent = Torrent(args.file)
    if args.show:
        torrent.show_metadata()
        exit(0)

    tracker = Tracker(torrent)
    for peer in tracker.peers:
        print(f"Peer ({peer.ip}, {peer.port}): {peer.handshake} {peer.rate}")
