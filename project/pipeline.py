import csv
import random
import string

from project.bwt import transform
from project.loaders import DictionaryLoader
from project.string_utils import levenshtein_distance


def main():
    words = DictionaryLoader()
    with open("runs.csv", "a", newline="") as runs:
        writer = csv.writer(runs)
        for word in words:
            position = random.randrange(len(word))
            replacement = random.choice(
                string.ascii_lowercase.replace(word[position], "")
            )
            new_word = word[:position] + replacement + word[position + 1:]
            distance = levenshtein_distance(transform(word), transform(new_word))
            writer.writerow([distance, len(word)])


if __name__ == "__main__":
    main()
