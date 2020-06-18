import os
import pathlib

import audio_metadata

MEDIA_PATH = os.path.expanduser('~/Music')
parsed_songs = []
for filepath in pathlib.Path(MEDIA_PATH).glob('**/*'):
    if filepath.is_file():
        try:
            filepath = filepath.absolute()
            metadata = audio_metadata.load(filepath)
            song_info = {"success": True, "name": metadata["tags"]["title"], "artist": metadata["tags"]["artist"], "path": filepath}
            print(metadata)
        except KeyError:
            print("no Metadata found for song:", filepath)
            songinfo = {"success": False}
        parsed_songs.append(song_info)
print(parsed_songs)
#"genre": metadata["tags"]["genre"]

