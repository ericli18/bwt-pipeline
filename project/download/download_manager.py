import hashlib
import shutil
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

DEFAULT_DOWNLOAD_DIR = ".cache/downloads"
USER_AGENT = "bwt-pipeline/0.1"


@dataclass
class DownloadConfig:
    download_dir: str = DEFAULT_DOWNLOAD_DIR
    extract_compressed_file: bool = False


class DownloadManager:
    def download(self, url: str, download_config: DownloadConfig | None = None) -> Path:
        """Download *url* once and optionally return its extraction directory."""
        config = download_config if download_config else DownloadConfig()
        cache_dir = Path(config.download_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / hashlib.sha256(url.encode()).hexdigest()

        if not cache_path.exists():
            start_time = datetime.now()
            # Some corpus hosts reject urllib's default user agent.
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            partial_path = cache_path.with_suffix(".partial")
            with (
                urllib.request.urlopen(request) as source,
                partial_path.open("wb") as target,
            ):
                shutil.copyfileobj(source, target)
            partial_path.replace(cache_path)
            duration = datetime.now() - start_time
            print(
                f"Downloaded corpus in {duration.total_seconds():.2f}s to {cache_path}"
            )

        if not config.extract_compressed_file:
            return cache_path

        extraction_dir = cache_path.with_suffix(".extracted")
        if not extraction_dir.exists():
            extraction_dir.mkdir(parents=True)
            with ZipFile(cache_path) as archive:
                archive.extractall(extraction_dir)
        return extraction_dir
