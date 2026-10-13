from project.download.download_manager import DownloadConfig, DownloadManager
from project.loaders import CORPORA


# Feel free to use this file to predownload everything. Not needed though.
def main():
    manager = DownloadManager()
    for corpus in CORPORA.values():
        path = manager.download(
            corpus.url, DownloadConfig(extract_compressed_file=True)
        )
        print(f"{corpus.name}: {path}")


if __name__ == "__main__":
    main()
