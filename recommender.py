import copy
import json
import os.path
import math
import threading
import time
from operator import itemgetter

import numpy as np
from scipy.spatial import distance

import mpd_connector

PATH_SONGTAGS = "song_tags.json"
PATH_USER_DATA = "user_data.json"
MPD_IP = "localhost"
MPD_PORT = 6600


class Recommender:
    def __init__(self):
        self.json_data = self.read_tags_from_json(PATH_SONGTAGS)
        self.song_vectors = self.create_song_feature_vectors()  # [(Valence, danceability, energy), title, interpreter]
        self.played_songs_session = []
        self.user_controller = UserController(PATH_USER_DATA, self.song_vectors)
        self.mpd = mpd_connector.MpdConnector(MPD_IP, MPD_PORT)
        t = threading.Thread(target=self._update_played_songs_session, daemon=True)
        t.start

    @staticmethod
    def read_tags_from_json(path):
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
            single_entry = (
                np.array([v for v in song["audio_features"].values()], dtype=float), song["song_name"],
                song["interpreter"])
            song_vector_list.append(single_entry)
        return song_vector_list

    def _update_played_songs_session(self): # TOTEST
        """
        Tracks all songs that were played this session. Only call this inside a thread.
        Updates every 30s.
        :return:
        """
        while True:
            current_song = self.mpd.get_current_song()  # TODO input: ip and port from mpd
            if self.played_songs_session:  # if list not empty
                if self.played_songs_session[-1] is not current_song:
                    self.played_songs_session.append(current_song)
            else:
                self.played_songs_session.append(current_song)
            print("current song list:", self.played_songs_session)
            print("sleeping 30s")
            time.sleep(30)

    def recommend_song_v1_old(self, user_controller):
        cold_start_recommend = self.cold_start(user_controller)
        if cold_start_recommend is not None:  # None if this is not a cold start
            return cold_start_recommend

        user_vector = user_controller.get_user_vector()
        min_dist = float("inf")
        min_track = None
        for song in self.song_vectors:
            eukl_dist = distance.euclidean(song[0], user_vector)
            print(eukl_dist)
            if eukl_dist < min_dist:
                min_dist = eukl_dist
                min_track = (song[1], song[2])  # (name, interpreter)
                # TODO if song not already recommended this session
        return min_track

    def recommend_song_v1(self):
        """
        recommend a song solely based on the song vectors, not taking into account the genres or artists
        :return: sorted list of euclidean distances with title and artist
        """
        cold_start_recommend = self.cold_start()
        if cold_start_recommend is not None:  # None if this is not a cold start
            return cold_start_recommend

        user_vector = self.user_controller.get_user_vector()
        euclidean_distance_list = []
        for song in self.song_vectors:
            eucl_dist = distance.euclidean(song[0], user_vector)
            euclidean_distance_list.append((eucl_dist, song[1], song[2]))
        return sorted(euclidean_distance_list, key=itemgetter(0))

    def cold_start(self):
        """
        Return the most popular song in the library if this is a cold start.
        It's a cold start, if there is no available user data.
        :return: None, if no coldstart, otherwise, recomended song
        """
        if self.user_controller.is_cold_start():
            # Take a guess based on popularity
            most_popular_song = ((), 0)
            for song in self.json_data:
                if most_popular_song[1] < song["popularity"]:
                    most_popular_song = ((song["song_name"], song["interpreter"]), song["popularity"])
                    if most_popular_song[1] == 100:  # 100 is the max value
                        return most_popular_song
            return most_popular_song[0]
        else:
            return None

    def choose_recommended_song(self):
        """
        compare the song vector with the user vector and get the n best matches.
        Take into account the genres
        Take into account the listened artists to slighly increase the chance the user gets a high familiarity high liking song,
        since these will make the user think the recommender understands his/her tastes (human evaluation of music recommender systems)

        :return: next recommended song
        """


class UserDataContainer:
    """
    This class is used to store the preferences of the user.
    """

    def __init__(self):
        self.song_count = 0
        self.vector_total = np.array([0, 0, 0, 0, 0, 0],
                                     dtype=float)  # (valence, danceability, energy, tempo, acousticness, speechiness)
        self.vector_avg = np.array([0, 0, 0, 0, 0, 0], dtype=float)  # self.vector_total / self.total_songs_played
        self.genres = []  # [("genre_name", times_played)]
        self.artists = []  # [("artist_name", times_played)


class UserController:
    """
    THis class controls the user preferences and saves all time preferences and session preferences as UserDataContainer.
    Genres and Artits can be returned as percentages, because displaying them as vectors would cause the most prevalent
    genre/artist to always be recommended.
    Session should be weighted more than overall tastes, since moods can greatly influence music tastes
    :param path_serialization: path to the json file the user profile is saved in
    """
    stats_all_time: UserDataContainer

    def __init__(self, path_serialization, song_vectors):
        self.path_serialization = path_serialization
        self.song_vectors = song_vectors

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
        for song in self.song_vectors:
            if song[1].strip().casefold() == currently_played_song["title"].strip().casefold() and song[
                2].strip().casefold() == currently_played_song["artist"].strip().casefold():
                matched_song = song  # matched song: [Valence, danceability, energy], songname, interpreter
                break
        if matched_song is None:
            print(currently_played_song, "has no matching song vector!")
            return  # ignore this song for the recommender
        new_song_vector = np.array(
            [matched_song[0][0], matched_song[0][1], matched_song[0][2], matched_song[0][3], matched_song[0][4],
             matched_song[0][5]], dtype=float)
        self.stats_all_time.vector_total += new_song_vector
        self.stats_all_time.song_count += 1
        self.stats_all_time.vector_avg = self.stats_all_time.vector_total / self.stats_all_time.song_count
        self.stats_session.vector_total += new_song_vector
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

    def get_session_weight(self):
        """
        weighting the session values according to how long that session is.
        This is done by the Formula: - 1/(1 + e^(0.8x -2)) + 0.9 this results in following values:
        x = 1: 0.13 ; x = 2: 0.3; x = 3: 0.49; x = 6: 0.84; x = 10: 0.89
        :return: weight_session : {0 <= weight_session <= 1}
        """
        if self.stats_session.song_count == 0:
            return 0.0
        else:
            return -1 / (1 + math.exp(0.8 * self.stats_session.song_count - 2)) + 0.9

    def get_user_vector(self):  # TOTEST
        """
        Calculate the averaged user vector, weighting the session values according to how long that session is.
        :return: user vector [valence, danceability, energy]
        """
        weight_session = self.get_session_weight()
        weight_all_time = 1 - weight_session
        weighted_vector_session = self.stats_session.vector_avg * weight_session
        weighted_vector_all_time = self.stats_all_time.vector_avg * weight_all_time
        return weighted_vector_all_time + weighted_vector_session

    def is_cold_start(self):
        """
        Its a cold start, if there is no user data present.
        :return: True if this is a cold start. Otherwise False
        """
        return (self.stats_all_time.song_count + self.stats_session.song_count) <= 0
