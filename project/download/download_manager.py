from zipfile import ZipFile
import hashlib
import shutil
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_DOWNLOAD_DIR = ".cache/downloads"


@dataclass
class DownloadConfig:
    download_dir: str = DEFAULT_DOWNLOAD_DIR
    extract_compressed_file: bool = False
    extraction_type: str = "zip"


class DownloadManager:
    def download(self, url: str, download_config: DownloadConfig | None):
        config = download_config if download_config else DownloadConfig()

        start_time = datetime.now()
        cache_dir = Path(config.download_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / hashlib.sha256(url.encode()).hexdigest()

        with urllib.request.urlopen(url) as source, cache_path.open("wb") as target:
            shutil.copyfileobj(source, target)

        if config.extract_compressed_file:
          extraction_dir = cache_path.with_suffix(".extracted")
          extraction_dir.mkdir(parents=True, exist_ok=True)
          with ZipFile(cache_path) as archive:
              archive.extractall(extraction_dir)

        duration = datetime.now() - start_time

        print("File downloaded in {} seconds at {}", duration, cache_path)

          
