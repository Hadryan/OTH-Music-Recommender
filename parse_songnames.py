import os
import re

songlist = open("songList.txt", "r")
for line in songlist:
    # print(line)
    path, file = os.path.split(line)
    if file[0] != ".":  # filter out hidden files
        file = os.path.splitext(file)[0]  # remove file extension
        file = re.sub("^(\d+\s-\s)", "", file)  # remove song number
        interpreter = re.split("/", path)[2]  # pathname like: Music/DSD Multichannel/Interpreter/Albumname/CD/Songname
        if re.sub(" ","", interpreter).lower() != "variousartists": #only remove artist from name if not various artists
            file = re.split("(\s-\s)", file)[-1] # remove the interpreter from name if present
        else:
            print("not stripped")
        print(interpreter)
        print(file)
songlist.close()
