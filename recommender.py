import copy
import json
import os.path
import numpy as np
from scipy.spatial import distance
import math

PATH_SONGTAGS = "song_tags.json"
PATH_USER_DATA = "user_data.json"


def recommend_song_v1():
    """
    recommend a song solely based on the song vectors, not taking into account the genres or artists
    :return: (str) songname + interpreter of recommended song
    """
    user_vector = UserController(PATH_USER_DATA).get_user_vector()
    min_dist = float("inf")
    min_track = None
    for song in SongData().song_vectors:
        eukl_dist = distance.euclidean(song[0], user_vector)
        print(eukl_dist)
        if eukl_dist < min_dist:
            min_dist = eukl_dist
            min_track = (song[1], song[2])  # (name, interpreter)
            # TODO if song not already recommended this session
    return min_track


def choose_recommended_song():
    """
    compare the song vector with the user vector and get the n best matches.
    Take into account the genres
    Take into account the listened artists to slighly increase the chance the user gets a high familiarity high liking song,
    since these will make the user think the recommender understands his/her tastes (human evaluation of music recommender systems)

    :return: next recommended song
    """


class SongData:
    """
    """

    def __init__(self):
        self.json_data = self.read_tags_from_json(PATH_SONGTAGS)
        self.song_vectors = self.create_song_feature_vectors()  # [(Valence, danceability, energy), name, interpreter]

    def read_tags_from_json(self, path):
        """
        TODO specify how that json has to look
        :param path: path to json file
        :return: returns a list of dicts as seen in json
         """
        with open(path, "r") as json_file:
            data = json.load(json_file)
        return data

    def create_song_feature_vectors(self):
        """
        create a single vector of the tracks features
        Song Vector: [(Valence, danceability, energy), songname, interpreter]
        :param song_data as returned by read_tags_from_json()
        :return: vector of track features
        """
        song_vector_list = []
        for song in self.json_data:
            single_entry = (np.array([song["audio_features"]["valence"], song["audio_features"]["danceability"],
                                      song["audio_features"]["energy"]]), song["song_name"], song["interpreter"])
            song_vector_list.append(single_entry)
        return song_vector_list


class UserDataContainer:
    """
    This class is used to store the preferences of the user.
    """

    def __init__(self):
        self.song_count = 0
        self.vector_total = np.array([0, 0, 0], dtype=float)  # (valence, danceability, energy)
        self.vector_avg = np.array([0, 0, 0], dtype=float)  # self.vector_total / self.total_songs_played
        self.genres = []  # [("genre_name", times_played)]
        self.artists = []  # [("artist_name", times_played)


class UserController:  # TODO CHange doc string
    """
    THis class controls the user preferences and saves all time preferences and session preferences as UserDataContainer.
    display listened genres as percentages, otherwise, if a user has lots of music, the most prevalent genre will always
    be recommended, since each song only has 1 genre at a time.
    Session should be weighted more than overall tastes, since moods can greatly influence music tastes
    (TODO: function that increases the weight of the session, the longer it has been going)
    :param path_serialization: path to the json file the user profile is saved in
    """
    stats_all_time: UserDataContainer

    def __init__(self, path_serialization):
        self.path_serialization = path_serialization
        self.song_data = SongData()

        self.stats_all_time = UserDataContainer()
        self.stats_session = UserDataContainer()

        self.deserialize()

    def deserialize(self):
        """
        if there is a user_data.json: set values from json
        :return:
        """
        if os.path.exists(self.path_serialization):
            with open(self.path_serialization, 'r') as json_file:
                serialized_class = json.load(json_file)
            self.stats_all_time.song_count = serialized_class["total_songs_played"]
            self.stats_all_time.vector_total = np.array(serialized_class["vector_total"])
            self.stats_all_time.vector_avg = np.array(serialized_class["vector_avg"])
            self.stats_all_time.genres = serialized_class["genres_total"]
            self.stats_all_time.artists = serialized_class["artists_total"]
        else:
            print("No user data found.")  # for testing

    def serialize_stats_all_time(self):
        stats_as_dict = {"total_songs_played": self.stats_all_time.song_count,
                         "vector_total": self.stats_all_time.vector_total.tolist(),
                         "vector_avg": self.stats_all_time.vector_avg.tolist(),
                         "genres_total": self.stats_all_time.genres,
                         "artists_total": self.stats_all_time.artists}

        with open(self.path_serialization, 'w') as json_file:
            json.dump(stats_as_dict, json_file, indent=4)

    def update_preferences(self, currently_played_song):
        """
        updates user preferences after every played song
        :param: currently_played_song: a dict that contains information about the current song.
                {"title": "", "artist": "", "genre": ""}
        :return:
        """
        matched_song = None
        for song in self.song_data.song_vectors:
            if song[1] == currently_played_song["title"] and song[2] == currently_played_song["artist"]:
                matched_song = song  # matched song: [Valence, danceability, energy], songname, interpreter
                break
        if matched_song is None:
            print(currently_played_song, "has no matching song vector!")
            return  # ignore this song for the recommender
        self.stats_all_time.vector_total += np.array([matched_song[0][0], matched_song[0][1], matched_song[0][2]],
                                                     dtype=float)
        self.stats_all_time.song_count += 1
        self.stats_all_time.vector_avg = self.stats_all_time.vector_total / self.stats_all_time.song_count
        self.stats_session.vector_total += np.array([matched_song[0][0], matched_song[0][1], matched_song[0][2]],
                                                    dtype=float)
        self.stats_session.song_count += 1
        self.stats_session.vector_avg = self.stats_session.vector_total / self.stats_session.song_count
        self._update_artists_or_genres(self.stats_all_time.genres, currently_played_song["genre"])
        self._update_artists_or_genres(self.stats_session.genres, currently_played_song["genre"])
        self._update_artists_or_genres(self.stats_all_time.artists, currently_played_song["artist"])
        self._update_artists_or_genres(self.stats_session.artists, currently_played_song["artist"])

    def _update_artists_or_genres(self, target_list, feature):
        """
        Updates the genres or artists list.
        :param target_list: the to be updated list, e.g. self.stats_session.artists
        :param feature: the song feature that fits to the selected list , e.g. the artists name
        :return:
        """
        for entry in target_list:
            if entry[0].strip().lower() == feature.strip().lower():
                entry[1] += 1
                return True
        target_list.append((feature, 1))
        return False

    def get_artist_percentages(self, scope):
        """
        :param scope: Can either be "session" or "all_time"
        :return:List of artists with the percentage of how often it was played compared to the total amount of played songs
        """
        if scope == "session":
            artist_list = copy.deepcopy(self.stats_session.artists)
            total_number = self.stats_session.song_count
        elif scope == "all_time":
            artist_list = copy.deepcopy(self.stats_all_time.artists)
            total_number = self.stats_all_time.song_count
        else:
            print("Unknown Scope. Please Use \"session\" or \"all_time\"")
            return
        for artist in artist_list:  # workinglist[artist_name, count], ...]
            artist[1] = (artist[1] / total_number) * 100

        return artist_list

    def get_genre_percentages(self, scope):
        """
        :param scope: Can either be "session" or "all_time"
        :return:List of genres with the percentage of how often it was played compared to the total amount of played songs
        """
        if scope == "session":
            genre_list = copy.deepcopy(self.stats_session.genres)
            total_number = self.stats_session.song_count
        elif scope == "all_time":
            genre_list = copy.deepcopy(self.stats_all_time.genres)
            total_number = self.stats_all_time.song_count
        else:
            print("Unknown Scope. Please Use \"session\" or \"all_time\"")
            return
        for genre in genre_list:  # workinglist[genre_name, count], ...]
            genre[1] = (genre[1] / total_number) * 100

        return genre_list

    def get_genre_percentages(self):
        """
        Take int account session_genre
        :return: List of genres with the percentage they were played compared to the total amount of played songs
        """

    def get_user_vector(self):
        """
        Calculate the averaged user vector, weighting the session values according to how long that session is.
        This is done by the Formula: - 1/(1 + e^(0.8x -2)) + 0.9 this results in following values:
        x = 1: 0.13 ; x = 2: 0.3; x = 3: 0.49; x = 6: 0.84; x = 10: 0.89
        :return: user vector [valence, danceability, energy]
        """
        session_factor = -1 / (1 + math.exp(0.8 * self.stats_session.song_count - 2)) + 0.9

