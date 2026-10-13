from project.loaders import CORPORA, CorpusLoader


def test_corpus_loader_reads_every_listed_file_in_order(tmp_path):
    corpus = CORPORA["canterbury"]
    for index, name in enumerate(corpus.files):
        (tmp_path / name).write_bytes(bytes([index]))

    documents = list(CorpusLoader(corpus, tmp_path))

    assert [document.name for document in documents] == list(corpus.files)
    assert [document.data for document in documents] == [
        bytes([index]) for index in range(len(corpus.files))
    ]
