import os
import re

songlist = open("songList.txt", "r")
for line in songlist:
    #print(line)
    file = os.path.basename(line)
    if file[0] != ".":  # filter out hidden names
        file = os.path.splitext(file)[0]  # remove file extension
        file = re.sub("^(\d+\s-\s)", "", file) # remove song number
        print(file)
songlist.close()
