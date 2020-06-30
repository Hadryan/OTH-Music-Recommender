import json
# from utils import NumpyEncoder
import numpy as np
import os.path

PATH_SONGTAGS = "song_tags.json"


def main():
    song_data = SongData()
    print(song_data.song_vectors)


class SongData:
    """
    """

    def __init__(self):
        self.json_data = self.read_tags_from_json(PATH_SONGTAGS)
        self.song_vectors = self.create_song_feature_vectors()

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


def choose_recommended_song():
    """
    compare the song vector with the user vector and get the n best matches.
    Take into account the genres
    Take into account the listened artists to slighly increase the chance the user gets a high familiarity high liking song,
    since these will make the user think the recommender understands his/her tastes (human evaluation of music recommender systems)

    :return: next recommended song
    """

class UserData:
    """
    This class is used to store the preferences of the user.
    Uses high level tags as vector. (e.g. danceability)
    display listened genres as percentages, otherwise, if a user has lots of music, the most prevalent genre will always
    be recommended, since each song only has 1 genre at a time.
    Session should be more weighted more than overall tastes, since moods can greatly influence music tastes
    (TODO: function that increases the weight of the session, the longer it has been going)

    Also tracks the listened to artists and recommends songs of often heard artists more frequently.

    :param path_serialization: path to the json file the user profile is saved in
    """

    def __init__(self, path_serialization):
        self.path_serialization = path_serialization
        self.song_data = SongData()

        self.total_songs_played = 0
        self.vector_total = np.array([0, 0, 0], dtype=float)  # (valence, danceability, energy)
        self.vector_avg = np.array([0, 0, 0], dtype=float)  # self.vector_total / self.total_songs_played
        self.genres_total = []  # [("genre_name", times_played)]
        self.artists_total = []  # [("artist_name", times_played)

        self.vector_session = np.array([0,0,0], dtype=float)  # TODO perhaps use a subclass to represent session
        self.session_songs_played = 0
        self.genres_session = []
        self.artists_session = []

        self.deserialize()

    def deserialize(self):
        """
        if there is a user_data.json: set values from json
        :return:
        """
        if os.path.exists(self.path_serialization):
            with open(self.path_serialization, 'r') as json_file:
                serialized_class = json.load(json_file)
            self.total_songs_played = serialized_class["total_songs_played"]
            self.vector_total = np.array(serialized_class["vector_total"])
            self.vector_avg = np.array(serialized_class["vector_avg"])
            self.genres_total = serialized_class["genres_total"]
            self.artists_total = serialized_class["artists_total"]
        else:
            print("No user data found.")  # for testing

    def serialize_user_data(self):
        class_as_dict = {"total_songs_played": self.total_songs_played, "vector_total": self.vector_total.tolist(),
                         "vector_avg": self.vector_avg.tolist(), "genres_total": self.genres_total,
                         "artists_total": self.artists_total}

        with open(self.path_serialization, 'w') as json_file:
            json.dump(class_as_dict, json_file, indent=4)

    def update_preferences(self, currently_played_song):
        """
        updates preferences after every played song
        :return:
        """
        matched_song = None
        for song in self.song_data.song_vectors:
            if song[1] == currently_played_song["title"] and song[2] == currently_played_song["artist"]:
                matched_song = song
                break
        if matched_song is None:
            print(currently_played_song, "has no matching song vector!")
            return  # ignore this song for the recommender
        self.vector_total += np.array([matched_song[0][0], matched_song[0][1], matched_song[0][2]], dtype=float)
        self.total_songs_played += 1
        self.vector_avg = self.vector_total / self.total_songs_played
        self._update_genre_and_artist(currently_played_song)

    def _update_genre_and_artist(self, currently_played_song):
        """
        updates the genres and artists list depending on the currently_played_song
        :param currently_played_song: dict object that stores artist and genre #TODO check if most songs have the genre tag set, otherwise will have to get this from spotify
        :return:
        """
        new_genre = currently_played_song["genre"]
        genre_existing = False
        new_artist = currently_played_song["artist"]
        artist_existing = False
        if new_genre is not None or "":
            for genre in self.genres_total:
                if genre[0].strip().lower() == new_genre.strip().lower():
                    genre[1] += 1
                    genre_existing = True
                    break
            if not genre_existing:
                self.genres_total.append(
                    (new_genre, 1))  # perhaps use a set list of genres instead of adding genres automatically
        if new_artist.lower() is not None or "" or "various artists":
            for artist in self.artists_total:
                if artist[0].strip().lower() == new_artist.strip().lower():
                    artist[1] += 1
                    artist_existing = True
                    break
            if not artist_existing:
                self.artists_total.append((new_artist, 1))

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


if __name__ == '__main__':
    main()
