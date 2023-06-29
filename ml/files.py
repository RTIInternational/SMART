def write(path, file):
    with open(path, "w") as w:
        for row in file.file:
            w.write(row)
