import os
import time

import tekore as tk
import json
import re
import mpd_connector

client_id = "08fce4b3fb2144838c7f65133d289fbc"
client_secret = "9011cc6827684eb783288bd04147140b"
redirect_uri = "http://localhost:8888"
refresh_token = "AQD2gsLOa6g984Kvt62WR2rT2rqJVzHIEN7GZWq23915TiKQQNpBKSQMTqoow11IoWRst3mBVbyh2GUKLrB6Us7AhNl25KWozaJpGIi2-WkUqUloiKmBsNTEG0da7b4wOcc"
MPD_IP = "localhost"
MPD_PORT = 6600
OUTPUT_PATH = "data/song_tags.json"
RELATED_ARTISTS_PATH = "data/related_artists.json"


def main():

    spotify = init()
    song_list = mpd_connector.MpdConnector(MPD_IP, MPD_PORT).get_all_songs()
    id_name_list = get_spotify_data(song_list, spotify)
    get_similiar_artists(id_name_list, spotify, RELATED_ARTISTS_PATH)
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


def get_spotify_data(songnames_dict, spotify):
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
                spotify_id_list.append({"artist": single_track_info["artist"], "title": single_track_info["title"],
                                        "popularity": track_paging_object.items[0].popularity,
                                        "id": track_paging_object.items[0].id, "genre": single_track_info["genre"],
                                        "album": single_track_info["album"], "date": single_track_info["date"],
                                        "artist_id": track_paging_object.items[0].artists[0].id})
            else:
                error_list.append(single_track_info)
        except Exception as e:
            print(e)
            time.sleep(1)
            print("wait 1s, api exception")
            error_list.append(single_track_info)
    print("Found on Spotify:", len(spotify_id_list), "/", len(songnames_dict))
    print(*error_list)
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


def get_similiar_artists(spotify_data, spotify, json_path):
    artist_dict = {}
    for song_info in spotify_data:
        related_artists = spotify.artist_related_artists(song_info["artist_id"])
        artists_realted = []
        for i in range(0, 3):  # just append the first 3 related artists
            artists_realted.append(related_artists[i].name)
        artist_dict[song_info["artist"]] = artists_realted
    print(artist_dict)
    save_as_json(artist_dict, json_path)
    return artist_dict



def match_high_level_tags(id_name_list, spotify):
    """
    :param id_name_list: from get_spotify_data
    :return: list of dict
    """
    for song_info in id_name_list:
        audio_features = spotify.track_audio_features(song_info["id"])
        reduced_audio_features = AudioFeatures(audio_features.valence, audio_features.danceability,
                                               audio_features.energy, _scale_tempo_down(audio_features.tempo),
                                               audio_features.acousticness,
                                               audio_features.speechiness)
        song_info["audio_features"] = reduced_audio_features.asdict()
        song_info.pop("id", None)
        song_info.pop("artist_id", None)
    print(id_name_list)
    return id_name_list


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
