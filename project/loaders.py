from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import nltk
from nltk.corpus import words

from project.download.download_manager import DownloadConfig, DownloadManager


class BaseLoader(ABC):
    @abstractmethod
    def __iter__(self):
        pass

    def get_iterator(self):
        return self.__iter__()


class DictionaryLoader(BaseLoader):
    def __iter__(self) -> Iterator[str]:
        try:
            entries = words.words("en")
        except LookupError:
            try:
                if not nltk.download("words", quiet=True, raise_on_error=True):
                    raise RuntimeError("NLTK could not download the words corpus")
                entries = words.words("en")
            except Exception as exc:
                raise RuntimeError(
                    "Unable to load the English words corpus. "
                    "Try downloading it manually with: "
                    "uv run python -m nltk.downloader words"
                ) from exc

        yield from entries


@dataclass(frozen=True)
class CorpusDocument:
    name: str
    data: bytes


@dataclass(frozen=True)
class Corpus:
    name: str
    url: str
    files: tuple[str, ...]


CORPORA = {
    corpus.name: corpus
    for corpus in (
        Corpus(
            name="calgary",
            url="http://www.data-compression.info/files/corpora/calgarycorpus.zip",
            files=(
                "bib",
                "book1",
                "book2",
                "geo",
                "news",
                "obj1",
                "obj2",
                "paper1",
                "paper2",
                "pic",
                "progc",
                "progl",
                "progp",
                "trans",
            ),
        ),
        Corpus(
            name="canterbury",
            url="https://corpus.canterbury.ac.nz/resources/cantrbry.zip",
            files=(
                "alice29.txt",
                "asyoulik.txt",
                "cp.html",
                "fields.c",
                "grammar.lsp",
                "kennedy.xls",
                "lcet10.txt",
                "plrabn12.txt",
                "ptt5",
                "sum",
                "xargs.1",
            ),
        ),
    )
}


class CorpusLoader(BaseLoader):
    def __init__(self, corpus: Corpus, corpus_dir: Path | None = None):
        self.corpus = corpus
        self.corpus_dir = corpus_dir

    def __iter__(self) -> Iterator[CorpusDocument]:
        corpus_dir = self.corpus_dir
        if corpus_dir is None:
            corpus_dir = DownloadManager().download(
                self.corpus.url,
                DownloadConfig(extract_compressed_file=True),
            )

        for name in self.corpus.files:
            path = corpus_dir / name
            try:
                data = path.read_bytes()
            except OSError as exc:
                raise RuntimeError(
                    f"{self.corpus.name} corpus file is missing or unreadable: {path}"
                ) from exc
            yield CorpusDocument(name=name, data=data)
