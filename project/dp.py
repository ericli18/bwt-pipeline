import math


def calculate_global_sensitivity(T: bytes, g: int):
    n = len(T)
    return 4 * math.sqrt(g * n * math.log2(n))


if __name__ == "__main__":
    print("Hello world")
