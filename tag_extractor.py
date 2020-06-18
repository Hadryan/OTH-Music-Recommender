import tekore as tk
import parse_songnames
import json
#import metadata_reader

client_id = "08fce4b3fb2144838c7f65133d289fbc"
client_secret = "9011cc6827684eb783288bd04147140b"
redirect_uri = "http://localhost:8888"
refresh_token = "AQD2gsLOa6g984Kvt62WR2rT2rqJVzHIEN7GZWq23915TiKQQNpBKSQMTqoow11IoWRst3mBVbyh2GUKLrB6Us7AhNl25KWozaJpGIi2-WkUqUloiKmBsNTEG0da7b4wOcc"


def main():
    #parse_songnames.parse_songlist_new("songList.txt")
    spotify = init()
    id_name_list = get_spotify_ids("songList.txt", spotify)
    list_with_high_level_tags = match_high_level_tags(id_name_list, spotify)
    save_as_json(list_with_high_level_tags)


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


def get_spotify_ids(path_songlist, spotify):
    track_list = parse_songnames.parse_songlist(path_songlist)
    print("starting api calls....")
    spotify_id_list = []
    error_list = []
    for single_track_info in track_list:
        track_paging_object, = spotify.search(single_track_info[0] + " " + single_track_info[1], limit=1)
        if len(track_paging_object.items) != 0:
            spotify_id_list.append(
                (single_track_info[0], single_track_info[1], single_track_info[2], track_paging_object.items[0].id))
        else:
            error_list.append(single_track_info)

    #    print(spotify_id_list)
    print("correct:", len(spotify_id_list))
    print("false:", len(error_list))
    #   for error in error_list:
    #      print(error)

    # try getting more results by omitting the interpreter
    for single_track_info in error_list:
        track_paging_object, = spotify.search(single_track_info[1], limit=1)
        if len(track_paging_object.items) != 0:
            spotify_id_list.append(
                (single_track_info[0], single_track_info[1], single_track_info[2], track_paging_object.items[0].id))
            error_list.remove(single_track_info)
    print("After second iteration:")
    print("correct:", len(spotify_id_list))
    print("false:", len(error_list))
    # for error in error_list:
    # print(error)
    print(spotify_id_list)
    return spotify_id_list


def match_high_level_tags(id_name_list, spotify):
    """
    :param id_name_list: list of tuples: [(interpreter, songname, orginal_path, spoitfy_id), ...] from get_spotify_ids
    :return: list of dict
    """
    high_level_dict_list = []
    for song_info in id_name_list:
        audio_features = spotify.track_audio_features(song_info[3])
        reduced_audio_features = AudioFeatures(audio_features.valence, audio_features.danceability,
                                               audio_features.energy)
        high_level_dict_list.append(
            {"song_name": song_info[1], "interpreter": song_info[0], "audio_features": reduced_audio_features.asdict()})
    print(high_level_dict_list)
    return high_level_dict_list

def save_as_json(high_level_dict_list):
    with open("song_tags.json", "w") as file_name:
        json.dump(high_level_dict_list, file_name)



class AudioFeatures:
    def __init__(self, valence, danceability, energy):
        self.valence = valence
        self.danceability = danceability
        self.energy = energy

    def asdict(self):
        return {"valence": self.valence, "danceability": self.danceability, "energy": self.energy}


if __name__ == '__main__':
    main()
