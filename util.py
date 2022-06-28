from collections import OrderedDict


def throw_error(message):
    print(f"Error: {message}")
    exit(1)


def populate_dict(dictionary, keys):
    data = OrderedDict()
    for key in keys:
        data[key] = dictionary[key] if key in dictionary else None
    return data


def format_size(size, binary=False):
    base = 1024 if binary else 1000
    unit = ["k", "k", "M", "G", "T", "P", "E", "Z", "Y"]
    unit = list(map(str.upper, unit)) if binary else unit
    i = 0
    while size > base:
        size /= base
        i += 1
    size = (size / base) if i == 0 else size
    return f"{round(size, 2)} {unit[min(i, 8)]}{'i' if binary else ''}B"
