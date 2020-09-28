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
import config_project
from SpotifyRecommender import tag_extractor


WEIGHT_ARTISTS = 0.2  # How strong artists are being factored into the recommendation compared to genres
WEIGHT_RELATED_ARTISTS = 1


class Recommender:
    def __init__(self):
        if not os.path.exists(config_project.PATH_SONG_DATA):
            logging.warning(
                "You need to extract song tags before initializing the recommender! Starting tag extraction now...")
            tag_extractor.TagExtractor()
        self.json_data = self.read_tags_from_json(config_project.PATH_SONG_DATA)
        self.song_vectors = self.create_song_feature_vectors()  # [(Valence, danceability, energy), title, interpreter]
        self.played_songs_session = []
        self.user_controller = UserDataController(config_project.PATH_USER_DATA, self.song_vectors)
        self.mpd = mpd_connector.MpdConnector(config_project.MPD_IP, config_project.MPD_PORT)
        t = threading.Thread(target=self._update_played_songs, daemon=True)
        t.start()


    @staticmethod
    def read_tags_from_json(path):
        """
        :param path: path to json file that was created using tag_extractor.py
        :return: returns a list of dicts as seen in json
         """
        try:
            with open(path, "r") as json_file:
                data = json.load(json_file)
            return data
        except FileNotFoundError:
            logging.error("SONG_TAGS NOT FOUND! Please run tag_extractor.py")

    def create_song_feature_vectors(self):
        """
        create a vector of the tracks audio features for every song in song_tags.json
        Song vector: [(Valence, danceability, energy, tempo, acousticness, speechiness), songname, interpreter]
        :param song_data as returned by read_tags_from_json()
        :return: List of Song vectors
        """
        song_vector_list = []
        for song in self.json_data:
            single_entry = (
                np.array([v for v in song["audio_features"].values()], dtype=float), song["title"],
                song["artist"], song["genre"])
            song_vector_list.append(single_entry)
        return song_vector_list

    def _update_played_songs(self):
        """
        Tracks all songs that were played this session. Only call this inside a thread.
        Updates every 30s.
        :return:
        """
        while True:
            time.sleep(10)
            try:
                current_song = self.mpd.get_current_song()
                if current_song:  # if there is a song currently playing
                    if self.played_songs_session:  # if this is not the first song played this session
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
                    self.played_songs_session)):  # dont recommend songs played this session!
                eucl_dist = distance.euclidean(song[0], user_vector)
                euclidean_distance_list.append(
                    {"score": eucl_dist, "title": song[1], "interpreter": song[2], "genre": song[3]})
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
        for song in songs_sorted_by_popularity: # so it has the same attribute as in the non cold start scenario
            song["interpreter"] = song["artist"]
            song["score"] = 0
        return sorted(songs_sorted_by_popularity, key=itemgetter("popularity"), reverse=True)

    def consider_genre_artist(self, distance_list):
        """
        Take into account the genres
        Take into account the listened artists to slightly increase the chance the user gets a high familiarity high liking song,
        since these will make the user think the recommender understands his/her tastes (human evaluation of music recommender systems)
        :param: distance_list: eukl. distances of song vectors to the user vector. Created by calling get_eucl_distance_list()
        :return: sorted list of songs, ordered from best match to worst
        """

        if self.user_controller.is_cold_start():
            return self.cold_start()

        percentages_genres = self.user_controller.get_percentages_genre_or_artist("genre")
        percentages_artists = self.user_controller.get_percentages_genre_or_artist("artist")
        for track in distance_list:
            score_reduction = 0  # optimal score = 0 -> reducing the score increases the chance it gets recommended
            if track["genre"] in percentages_genres:  # if genre in listened to genres
                score_reduction = track["score"] * percentages_genres[
                    track["genre"]]  # score = score - (score * genre percentage)
            if track["interpreter"] in percentages_artists:  # if artist in listened to artists
                score_reduction += track["score"] * WEIGHT_ARTISTS * percentages_artists[track["interpreter"]]
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
        score_list = self.consider_genre_artist(
            self.get_eucl_distance_list(self.song_vectors, self.user_controller.get_user_vector()))
        genre_list = []
        for song in score_list:
            if equals(genre, song["genre"]):
                genre_list.append(song)
        return genre_list

    def recommend_song_mood(self, mood):
        """
        This is an experimental mood recommender.
        The quality of the results is very dependant on the quality of the spotify tags.
        :param mood: possible moods: positive, negative
        :return: sorted how recommended the songs are in descending order.
        """
        new_user_vector = copy.copy(self.user_controller.get_user_vector())
        if equals(mood, "positive"):  # energy + valence high
            new_user_vector[0] = 1  # set valence to max
            if new_user_vector[3] * 1.3 < 1:
                new_user_vector[3] = new_user_vector[3] * 1.3  
            else:
                new_user_vector[3] = 1
        elif equals(mood, "negative"):  # low valence
            new_user_vector[0] = 0  # set valence to min
        else:
            raise ValueError('Unknown parameter for recommend_song_mood.', mood)
        score_list = self.get_eucl_distance_list(self.song_vectors, new_user_vector)
        return self.consider_genre_artist(score_list)

    def recommend_genre_or_mood(self, input_value):
        """
        this method determines whether to call the genre or mood recommendation.
        :return: recommended song
        """
        if equals(input_value, "positive") or equals(input_value, "negative") or equals(input_value, "angry"):
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
        self.genres = {}  # Dict: Key=Genre_name, Value=Times_Played
        self.artists = {}  # Dict: Key=Artist_name, Value=Times_Played


class UserDataController:
    """
    THis class controls the user preferences and saves all time preferences and session preferences as UserDataContainer.
    Genres and Artists can be returned as percentages.
    Session should be weighted more than overall tastes, since moods can greatly influence music tastes
    :param path_serialization: path to the json file the user profile is saved in song_vectors: Song vectors red from
    song_tags.json
    """

    def __init__(self, path_serialization, song_vectors):
        self.path_serialization = path_serialization
        self.song_vectors = song_vectors
        self.related_artists = {}

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
            logging.warning("No user data found, creating new profile")
        if os.path.exists(config_project.PATH_RELATED_ARTISTS):
            with open(config_project.PATH_RELATED_ARTISTS, 'r') as json_file:
                self.related_artists = json.load(json_file)
        else:
            logging.error("Related artists file not found")

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
                    matched_song = song  # matched song: [valence, ...], songname, interpreter
                    break
        except KeyError:
            logging.error("currently_played_song is missing title or interpreter!")
            return
        if matched_song is None:
            logging.warning(termcolor.colored(currently_played_song["title"] + ", " + currently_played_song[
                "artist"] + " has no matching song vector! Please update your song tags!", "yellow"))
            return  # ignore this song for the recommender
        if "genre" not in currently_played_song:
            logging.warning(termcolor.colored(currently_played_song["title"] + ", " + currently_played_song[
                "artist"] + " has no genre! Not adding this song to the user profile. Please update your song tags and check if your songs have the required metadata!",
                                              "yellow"))
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
        self._update_genres(self.stats_all_time.genres, currently_played_song["genre"])
        self._update_genres(self.stats_session.genres, currently_played_song["genre"])
        self._update_artists(self.stats_all_time.artists, currently_played_song["artist"])
        self._update_artists(self.stats_session.artists, currently_played_song["artist"])

    @staticmethod
    def _update_genres(target_dict, feature):
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

    def _update_artists(self, target_dict, artist_name):
        """
        Updates the artists and the related_artists, taken from the spotify api.
        The Weight of related_artists is
        determined by the global variable WEIGHT_RELATED_ARTISTS.
        :param target_dict: the to be updated dict, e.g. self.stats_session.artists
        :param artist_name: the song feature that fits to the selected list , e.g. the artists name
        """
        try:
            related_artists_selection = copy.copy(self.related_artists[str(artist_name)])
            for i in range(len(related_artists_selection)):
                related_artists_selection[i] = [related_artists_selection[i], False]  # false for not found yet
        except KeyError:
            logging.warning("No related artists found for", artist_name)

        if target_dict:  # check if not empty
            found = False
            for key in target_dict.copy():  # copy to avoid RuntimeError: Dict changed size during iteration
                for related_artist in related_artists_selection:
                    if related_artist[1]:  # if already found
                        continue
                    elif equals(str(key), related_artist[0]):
                        target_dict[key] += WEIGHT_RELATED_ARTISTS
                        related_artist[1] = True
                        break
                if equals(str(key), artist_name):
                    target_dict[key] += 1
                    found = True
            if not found:
                target_dict[artist_name] = 1
            for related_artist in related_artists_selection:
                if not related_artist[1]:
                    target_dict[related_artist[0]] = WEIGHT_RELATED_ARTISTS
        else:
            target_dict[artist_name] = 1

    def get_artist_percentages(self, scope):
        """
        Not in use right now.
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
        for artist in artist_list:
            artist[1] = (artist[1] / total_number) * 100

        return artist_list

    def get_genre_percentages(self, scope):
        """
        Not in use right now.
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
        the weighted percentages are calculated by dividing the times an item is recorded (e.g. times a genre was played)
        by the amount of songs played. This is done for the session and all time stats.
        These 2 percentages for every genre/artist are then each multiplied by their factor (calculated in get_session_factor())
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
        This is done via the function: - 1/(1 + e^(0.8x -2.19)) + 0.9 this results in following values:
        x = 1: 0.09 ; x = 2: 0.26; x = 3: 0.45; x = 6: 0.83; x = 20: 0.90
        :return: weight_session : {0 <= weight_session <= 0.9}
        """
        if self.stats_session.song_count == 0:
            return 0.0
        else:
            return round(-1 / (1 + math.exp(0.8 * self.stats_session.song_count - 2.19)) + 0.9, 2)

    def get_user_vector(self):
        """
        Calculate the averaged user vector, weighting the session values according to how long that session is.
        :return: user vector
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
