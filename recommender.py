import numpy as np


def read_tags_from_json(path):
    """
    Read all the tags saved for all processed songs
    :param path: path to json file
    :return: returns a list of dicts as seen in json
    """


def create_song_feature_vectors():
    """
    create a single vector of the tracks features
    :return: vector of track features
    """

def choose_recommended_song():
    """
    compare the song vector with the user vector and get the n best matches.
    Take into account the
    Take into account the listened artists to slighly increase the chance the user gets a high familiarity high liking song,
    since these will make the user think the recommender understands his/her tastes (human evaluation of music recommender systems)

    :return: next recommended song
    """



class UserData:
    """
    This class is used to store the prefernces of the user.
    Uses high level tags as vector. (e.g. danceability)
    display listened genres as percentages, otherwise, if a user has lots of music, only the most prevalent genre will
    be recommended, since one song only has 1 genre at a time.
    Session should be more weighted more than overall tastes, since moods can greatly influence music tastes
    (TODO: function that increases the weight of the session, the longer it has been going)

    Also tracks the listened to artists and recommends songs of often heard artists more often.
    """

    def __init__(self, path_json):
        self.json_data
        self.vector
        self.total_valence
        self.total_danceability
        self.total_energy
        self.session_valence # TODO perhaps use a subclass to represent session
        self.session_danceability
        self.session_energy
        self.session_genre
        self.genres # list of genres with times played
        self.artists #list of artists with the time their songs were played
        self.total_songs_played

    def update_preferences(self):
        """
        updates preferences after every played song
        :return:
        """

    def get_artist_percentages(self):
        """
        :return: List of artists with the percentage of how often it was played compared to the total amount of played songs
        """

    def get_genre_percentages(self):
        """
        Take int account session_genre
        :return: List of genres with the percentage they were played compared to the total amount of played songs
        """
    def calculate_user_vector(self):
        """
        Calculate the non normalized user vector, taking into account the session values.
        :return: non normalized user vector
        """

    def get_normalized_user_vector(self):
        """
        normalize the user vector, so it is comparable to the song vectors
        :return: user vector
        """
        self.calculate_user_vector()