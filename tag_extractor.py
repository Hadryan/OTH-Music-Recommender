import os
import time

import tekore as tk
import parse_songnames
import json
import re
import metadata_reader
import mpd_connector

client_id = "08fce4b3fb2144838c7f65133d289fbc"
client_secret = "9011cc6827684eb783288bd04147140b"
redirect_uri = "http://localhost:8888"
refresh_token = "AQD2gsLOa6g984Kvt62WR2rT2rqJVzHIEN7GZWq23915TiKQQNpBKSQMTqoow11IoWRst3mBVbyh2GUKLrB6Us7AhNl25KWozaJpGIi2-WkUqUloiKmBsNTEG0da7b4wOcc"
MEDIA_PATH = os.path.expanduser('~/Music/Lieder_HighResolutionAudio')
MPD_IP = "localhost"
MPD_PORT = 6600
OUTPUT_PATH = "song_tags.json"


def main():
    spotify = init()
    song_list = mpd_connector.MpdConnector(MPD_IP, MPD_PORT).get_all_songs()
    id_name_list = get_spotify_ids_mpd_tags(song_list, spotify)
    list_with_high_level_tags = match_high_level_tags(id_name_list, spotify)
    save_as_json(list_with_high_level_tags, OUTPUT_PATH)


def init():
    """
    Initialize + authorize
    :return: spotify object on which api methods can be called
    """
    cred = tk.RefreshingCredentials(client_id, client_secret, redirect_uri)
    app_token = cred.request_client_token()
    user_token = cred.refresh_user_token(refresh_token)
    sender = tk.RetryingSender(sender=tk.CachingSender())
    spotify = tk.Spotify(user_token, max_limits_on=True, sender=sender)
    return spotify


def get_spotify_ids_mpd_tags(songnames_dict, spotify):
    """
    Getting the spotify ids by searching for artists and songnames parsed from the mpd tags
    :param songnames_dict:
    :param spotify:
    :return:
    """
    songnames_dict = _remove_brackets(songnames_dict)
    print("starting api calls....")
    spotify_id_list = []
    error_list = []
    for single_track_info in songnames_dict:
        try:  # to catch all api exceptions
            track_paging_object, = spotify.search(single_track_info["title"] + " " + single_track_info["artist"],
                                                  limit=1)
            if len(track_paging_object.items) != 0:
                spotify_id_list.append((
                    single_track_info["artist"], single_track_info["title"], track_paging_object.items[0].popularity,
                    track_paging_object.items[0].id, single_track_info["genre"]))
            else:
                error_list.append(single_track_info)
        except Exception as e:  # TODO check doc what specific exception is being thrown
            print(e)
            time.sleep(1)
            print("wait 1s, api exception")
            error_list.append(single_track_info)
    print("correct:", len(spotify_id_list))
    print("false:", len(error_list))
    print(*error_list, sep="\n")
    return spotify_id_list


def _remove_brackets(dict_list):
    """
    remove the brackets from song and artist names, to increase the chance of a match on spotify
    :param dict_list:
    :return:
    """
    for song in dict_list:
        song["title"] = re.sub("\((.*?)\)", "", song["title"]).strip()
        song["artist"] = re.sub("\((.*?)\)", "", song["artist"]).strip()
    return dict_list


def match_high_level_tags(id_name_list, spotify):
    """
    :param id_name_list: list of tuples: [(interpreter, songname, popularity, spoitfy_id), ...] from get_spotify_ids
    :return: list of dict
    """
    high_level_dict_list = []
    for song_info in id_name_list:
        audio_features = spotify.track_audio_features(song_info[3])
        reduced_audio_features = AudioFeatures(audio_features.valence, audio_features.danceability,
                                               audio_features.energy, _scale_tempo_down(audio_features.tempo), audio_features.acousticness,
                                               audio_features.speechiness)
        high_level_dict_list.append(
            {"song_name": song_info[1], "interpreter": song_info[0], "popularity": song_info[2], "genre": song_info[4],
             "audio_features": reduced_audio_features.asdict()})
    print(high_level_dict_list)
    return high_level_dict_list

def _scale_tempo_down(tempo_in_bpm):
    """
    Scale Tempo attribute down to a scale from 0 - 1. Max BPM (Beats per minute) is assumed to be 225, since its extremely
    rare for a song to have a higher BPM
    """
    max_bpm = 225
    if tempo_in_bpm > max_bpm:
        tempo_in_bpm = max_bpm
    return round(tempo_in_bpm / max_bpm, 3)

def save_as_json(high_level_dict_list, save_path):
    with open(save_path, "w") as file_name:
        json.dump(high_level_dict_list, file_name)


class AudioFeatures:
    def __init__(self, valence, danceability, energy, tempo, acousticness, speechiness):
        self.valence = valence
        self.danceability = danceability
        self.energy = energy
        self.tempo = tempo
        self.acousticness = acousticness
        self.speechiness = speechiness

    def asdict(self):
        return {"valence": self.valence, "danceability": self.danceability, "energy": self.energy, "tempo": self.tempo,
                "acousticness": self.acousticness, "speechiness": self.speechiness}


if __name__ == '__main__':
    main()
