import shutil


def write(path, file):
    try:
        with open(path, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
    finally:
        file.file.close()
