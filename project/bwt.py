def rotate_string(string: str, rotations: int) -> str:
    return string[rotations:] + string[:rotations]

sentinel = '\0'

def transform(input: str):
    input += sentinel
    rotated_strings = [rotate_string(input, i) for i in range(0, len(input))]
    sorted_strings = sorted(rotated_strings)
    output = ''.join([string[-1] for string in sorted_strings])
    return output

def reconstruct(bwt: str) -> str:
    counts = {}
    for c in bwt:
        counts[c] = counts.get(c, 0) + 1

    C = {}
    total = 0

    for c in sorted(counts):
        C[c] = total
        total += counts[c]

    seen = {}
    rank = []

    for c in bwt:
        rank.append(seen.get(c, 0))
        seen[c] = seen.get(c, 0) + 1

    def lf(i):
        c = bwt[i]
        return C[c] + rank[i]

    r = bwt.index(sentinel)
    output = []

    for _ in range(len(bwt) - 1):
        r = lf(r)
        output.append(bwt[r])

    return ''.join(reversed(output))
