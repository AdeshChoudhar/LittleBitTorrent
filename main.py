from sys import exit 

from Torrent import Torrent
from util import parse_arguments


if __name__ == "__main__":
    args = parse_arguments()

    torrent = Torrent(args.file)
    if args.show:
        torrent.show_metadata()
        exit(0)
