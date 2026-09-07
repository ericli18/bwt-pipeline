from abc import ABC, abstractmethod
from collections.abc import Iterator

import nltk
from nltk.corpus import words


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
