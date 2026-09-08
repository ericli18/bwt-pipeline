from project.download.download_manager import DownloadConfig, DownloadManager


def main():
    print("Hello from bwt-pipeline!")
    manager = DownloadManager()
    manager.download(
        "http://www.data-compression.info/files/corpora/calgarycorpus.zip",
        DownloadConfig(extract_compressed_file=True, extraction_type="zip"),
    )


if __name__ == "__main__":
    main()
