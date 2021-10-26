# fshelper.py
# Provides simplified file access methods

import os


def list_files(path):
    result = os.listdir(path)
    return result


def create(path):
    result = None

    try:
        result = open(path, mode='x')
        print("Created file ", path)
    except OSError as e:
        print("Couldn't create file ", path, " due to exception ", e)
    finally:
        result.close()

    return


def delete(path):
    if os.path.exists(path):
        os.remove(path)
        print("Deleted file ", path)
    else:
        print("File ", path, " does not exist")
    return


def read_data(path):
    file = None

    try:
        file = open(path, mode='r')
        result = file.read()

    except Exception as e:
        print("Couldn't read file ", path, " due to exception ", e)
        result = ""
    finally:
        file.close()

    return result


def move(curpath, newpath):
    if os.path.exists(newpath):
        print("Destination file already exists.")
    elif not os.path.exists(curpath):
        print("Source file does not exist")
    else:
        data = read_data(curpath)

        newfile = open(newpath, mode='x')
        newfile.write(data)

        os.remove(curpath)

    return
