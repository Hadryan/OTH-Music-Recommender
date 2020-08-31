import pathlib

import audio_metadata


def read_metadata(path):
    """
    :param path: path object, e.g. os.path.expanduser('~/Music/Lieder_HighResolutionAudio')
    :return: [{"success": , "name": , "artist": , "path:"}, {...}
    """
    parsed_songs = []
    for filepath in pathlib.Path(path).glob('**/*'):
        if filepath.is_file():
            try:
                filepath = filepath.absolute()
                metadata = audio_metadata.load(filepath)
                song_info = {"success": True, "name": metadata["tags"]["title"][0], "artist": metadata["tags"]["artist"][0],
                             "path": filepath}
                # print(metadata["tags"]["genre"])
            except KeyError:
                print("no Metadata found for song:", filepath)
                song_info = {"success": False, "path": filepath}
            parsed_songs.append(song_info)

    print(parsed_songs)
    return parsed_songs
    # "genre": metadata["tags"]["genre"]
