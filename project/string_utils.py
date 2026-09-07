def levenshtein_distance(a: str, b: str) -> int:
    if len(a) > len(b):
        a, b = b, a

    distances = range(len(a) + 1)
    for i2, c2 in enumerate(b):
        distances_ = [i2+1]
        for i1, c1 in enumerate(a):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

