import copy
import json
import os.path
import math
import threading
import time
import logging
import termcolor
from operator import itemgetter

import numpy as np
from scipy.spatial import distance

import mpd_connector

FACTOR_ARTISTS = 0.4  # How strong artists are being factored into the recommendation compared to genres
PATH_SONGTAGS = "data/song_tags.json"
PATH_USER_DATA = "data/user_data.json"
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
        t.start()

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
                song["interpreter"], song["genre"])
            song_vector_list.append(single_entry)
        return song_vector_list

    def _update_played_songs_session(self):
        """
        Tracks all songs that were played this session. Only call this inside a thread.
        Updates every 30s.
        :return:
        """
        while True:
            time.sleep(10)
            try:
                current_song = self.mpd.get_current_song()
                if self.played_songs_session and current_song:  # if list and current_song not empty
                    if self.played_songs_session[-1] != current_song:
                        self.played_songs_session.append(current_song)
                        self.user_controller.update_preferences(current_song)
                        self.user_controller.serialize_stats_all_time()
                else:
                    self.played_songs_session.append(current_song)
            except KeyError:
                logging.debug("Couldn't get current song. Probably no song currently playing")

    def get_eucl_distance_list(self, song_vectors, user_vector):
        """
        recommend a song solely based on the song vectors, not taking into account the genres or artists
        :return: sorted list of sublists consisting of euclidean distances with title and artist
        """
        if self.user_controller.is_cold_start():
            return self.cold_start()

        euclidean_distance_list = []
        for song in song_vectors:
            if not (string_in_list_of_dicts("title", song[1], self.played_songs_session) and string_in_list_of_dicts(
                    "artist", song[2],
                    self.played_songs_session)):  # dont recommend songs played this session! TOTEST: what happens if played_songs_empty
                eucl_dist = distance.euclidean(song[0], user_vector)
                euclidean_distance_list.append({"score": eucl_dist, "song_name": song[1], "interpreter": song[2], "genre": song[3]})
        return sorted(euclidean_distance_list, key=itemgetter("score"))

    def cold_start(self):
        """
        Return the most popular song in the library if this is a cold start.
        It's a cold start, if there is no available user data.
        :return: None, if no cold start, otherwise, recomended song
        """
        # Take a guess based on popularity
        songs_sorted_by_popularity = copy.deepcopy(self.json_data)
        logging.info("Cold Start. Recommending by popularity")
        print(sorted(songs_sorted_by_popularity, key=itemgetter("popularity"), reverse=True))
        return sorted(songs_sorted_by_popularity, key=itemgetter("popularity"), reverse=True)

    def consider_genre_artist(self, distance_list):
        """
        Take into account the genres
        Take into account the listened artists to slighly increase the chance the user gets a high familiarity high liking song,
        since these will make the user think the recommender understands his/her tastes (human evaluation of music recommender systems)
        :param: distance_list: eukl. distances of songvectors to the user vector. Created by calling get_eucl_distance_list()
        :return: sorted list of songs, ordered from best match to worst
        """
        if self.user_controller.is_cold_start():
            return self.cold_start()

        percentages_genres = self.user_controller.get_percentages_genre_or_artist("genre")
        percentages_artists = self.user_controller.get_percentages_genre_or_artist("artist")
        for track in distance_list:
            score_reduction = 0  # optimal score = 0 -> reducing it increases the chance it gets recommended
            if track["genre"] in percentages_genres:  # if genre in listened to genres
                score_reduction = track["score"] * percentages_genres[track["genre"]]  # score = score - (score * genre percentage)
            if track["interpreter"] in percentages_artists:  # if artist in listened to artists
                score_reduction += track["score"] * FACTOR_ARTISTS * percentages_artists[track["interpreter"]]
            track["score"] = track["score"] - score_reduction

        return sorted(distance_list, key=itemgetter("score"))

    def recommend_song(self):
        """
        recommend a song. No restrictions.
        :return:
        """
        distance_list = self.get_eucl_distance_list(self.song_vectors, self.user_controller.get_user_vector())
        return self.consider_genre_artist(distance_list)

    def recommend_song_genre(self, genre):
        """
        recommend a song of a specified genre
        :param genre: genre as string
        :return: sorted list of recommendations
        """
        score_list = self.consider_genre_artist(self.get_eucl_distance_list(self.song_vectors, self.user_controller.get_user_vector()))
        genre_list = []
        for song in score_list:
            if equals(genre, song["genre"]):
                genre_list.append(song)
        return genre_list

    def recommend_song_mood(self, mood):
        """
        This is an experimental mood recommender.
        The quality of the results is very dependant on the quality of the spotify tags.
        :param mood: possible moods: positive, negative, angry
        :return: sorted how recommended the songs are in descending order.
        """
        new_user_vector = copy.copy(self.user_controller.get_user_vector())
        if mood == "positive": # energy + valence high
            new_user_vector[0] = 1  # set valence to max
            if new_user_vector[3] * 1.3 < 1:
                new_user_vector[3] = new_user_vector[3] * 1.3 # also increase the energy value
            else:
                new_user_vector[3] = 1
        elif mood == "negative": # low valence
            new_user_vector[0] = 0  # set valence to min
        elif mood == "angry": # Angry: Low valence, high energy #TODO perhaps remove, not working very well, perhaps better with more songs
            new_user_vector[0] = 0
            new_user_vector[3] = 1
        else:
            raise ValueError('Unknown parameter for recommend_song_mood.', mood)
        score_list = self.get_eucl_distance_list(self.song_vectors, new_user_vector)
        #print(score_list)
        return self.consider_genre_artist(score_list)

    def recommend_genre_or_mood(self, input_value):
        """
        this method determines whether to call the genre or mood recommendation.
        :return: recommended song
        """
        if input_value == ("postive" or "negative" or "angry"):
            logging.info("calling mood recommender.")
            return self.recommend_song_mood(input_value)
        else:
            logging.info("calling genre recommender")
            return self.recommend_song_genre(input_value)


class UserDataContainer:
    """
    This class is used to store the preferences of the user.
    """

    def __init__(self):
        self.song_count = 0
        self.vector_total = np.array([0, 0, 0, 0, 0, 0],
                                     dtype=float)  # (valence, danceability, energy, tempo, acousticness, speechiness)
        self.vector_avg = np.array([0, 0, 0, 0, 0, 0], dtype=float)  # self.vector_total / self.total_songs_played
        self.genres = {}  # [("genre_name", times_played)]
        self.artists = {}  # [("artist_name", times_played)


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
        try:
            for song in self.song_vectors:
                if equals(song[1], currently_played_song["title"]) and equals(song[2], currently_played_song["artist"]):
                    matched_song = song  # matched song: [Valence, danceability, energy], songname, interpreter
                    break
        except KeyError:
            logging.error("currently_played_song is missing title or interpreter!")
            return
        if matched_song is None:
            logging.warning(termcolor.colored(currently_played_song["title"] + ", " + currently_played_song[
                "artist"] + " has no matching song vector! Not adding this song to the user profile.", "yellow"))
            return  # ignore this song for the recommender
        if "genre" not in currently_played_song:
            logging.warning(termcolor.colored(currently_played_song["title"] + ", " + currently_played_song[
                "artist"] + " has no genre! Not adding this song to the user profile.", "yellow"))
            return
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

    @staticmethod
    def _update_artists_or_genres(target_dict, feature):
        """
        Updates the genres or artists list.
        :param target_dict: the to be updated dict, e.g. self.stats_session.artists
        :param feature: the song feature that fits to the selected list , e.g. the artists name
        """
        if target_dict:  # check if not empty
            found = False
            for key in target_dict.copy():  # copy to avoid RuntimeError: Dict changed size during iteration
                if equals(str(key), feature):
                    target_dict[key] += 1
                    found = True
            if not found:
                target_dict[feature] = 1
        else:
            target_dict[feature] = 1

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

    def get_percentages_genre_or_artist(self, genre_or_artist):
        if genre_or_artist == "artist":
            return self.calculate_weighted_percentages(self.stats_session.artists, self.stats_all_time.artists)
        elif genre_or_artist == "genre":
            return self.calculate_weighted_percentages(self.stats_session.genres, self.stats_all_time.genres)
        else:
            logging.error("Invalid parameter for get_percentages_genre_or_artist(genre_or_artist)."
                          " genre_or_artist as to be \"artist\" or \"genre\"")
            return None

    def calculate_weighted_percentages(self, dict_session, dict_all_time):
        """
        the weighted percantages are calculated by dividing the times an item is recorded (e.g. times a genre was played)
        by the amount of songs played. This is done for the session and all time stats.
        These 2 percentages for every genre are then each multiplied by their factor (calculated in get_session_factor())
        and at last added up for a weighted percentage.
        :return: {item: percentage, ...}
        """
        weight_session = self.get_session_weight()
        dict_session = copy.copy(dict_session)
        dict_all_time = copy.copy(dict_all_time)

        if dict_session:
            for key, value in dict_session.items():
                dict_session[key] = value / self.stats_session.song_count

        if dict_all_time:
            for key, value in dict_all_time.items():
                dict_all_time[key] = value / self.stats_all_time.song_count
        else:
            logging.exception(
                "Please check is_cold_start() before calling this method. This method should not be called"
                "if is_cold_start() returns true")

        for key, value in dict_all_time.items():
            if key in dict_session:
                dict_all_time[key] = (value * (1 - weight_session)) + (dict_session[key] * weight_session)
            else:
                dict_all_time[key] = (value * (1 - weight_session))

        return dict_all_time

    def get_session_weight(self):
        """
        weighting the session values according to how long that session is.
        This is done via the function: - 1/(1 + e^(0.8x -2)) + 0.9 this results in following values:
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


def equals(str1, str2):
    """
    compares 2 Strings, case insensitive and without leading or trailing whitespaces.
    """
    return str1.strip().casefold() == str2.strip().casefold()


def string_in_list_of_dicts(key, search_value, list_of_dicts):
    """
    Returns True if search_value is list of dictionaries at specified key.
    Case insensitive and without leading or trailing whitespaces.
    :return: True if found, else False
    """
    for item in list_of_dicts:
        if equals(item[key], search_value):
            return True
    return False
