from Torrent import Torrent


if __name__ == "__main__":
    file = input("Torrent file: ")

    torrent = Torrent(file)
    torrent.show_metadata()
