import time

import pytest
import recommender
import numpy as np
import json
from scipy.spatial import distance
import mpd_connector
import termcolor
import logging


def main():
    recommender_object = recommender.Recommender()
    recommender_object.played_songs_session = [{'title': 'People Get Ready', 'artist': 'One Love', 'genre': 'Reggae'},
                                               {'title': 'Too Long / Steam Machine', 'artist': 'Daft Punk',
                                                'genre': 'Electronica'},
                                               {'title': 'Thing Called Love', 'artist': 'Land Of Giants',
                                                'genre': 'Alternative'}]
    test_updating_user_information(recommender_object.user_controller)
    test_recommender_v1(recommender_object)
    # time.sleep(8)

    print(recommender_object.user_controller.get_percentages_genre_or_artist("genre"))
    print(recommender_object.user_controller.get_percentages_genre_or_artist("artist"))
    print(recommender_object.choose_recommended_song())
    # mpd = recommender_object.mpd
    # mpd.add_all_to_queue()
    # mpd.play_specific_song(2)
    """
    mpd.play_next_song()
    time.sleep(8)
    mpd.play_next_song()
    time.sleep(9)
    mpd.play_next_song()
    print(recommender_object.played_songs_session)
    mpd.pause()
    """
    # mpd_connector.test_mpd()
    # test_serialization()


def test_recommender_v1(recommender_object):
    print(recommender_object.get_eucl_distance_list(recommender_object.song_vectors,
                                                    recommender_object.user_controller.get_user_vector()))


def test_updating_user_information(user_controller):
    currently_played_song = {"title": "Grind", "artist": "Tangerine Dream", "genre": "Testgenre"}
    currently_played_song2 = {"title": "People Get Ready", "artist": "One Love", "genre": "Raggea"}
    currently_played_song3 = {"title": "She Used To Love Me A Lot", "artist": "Johnny Cash", "genre": "Country"}
    currently_played_song4 = {"title": "Thing Called Love", "artist": "Land of Giants", "genre": "Alternative"}
    user_controller.update_preferences(currently_played_song)
    user_controller.update_preferences(currently_played_song2)
    user_controller.update_preferences(currently_played_song3)
    user_controller.update_preferences(currently_played_song4)
    user_controller.serialize_stats_all_time()


def test_session_veighting(number_session):
    result = -1 / (1 + np.math.exp(0.8 * number_session - 2)) + 0.9
    print(result)


if __name__ == '__main__':
    main()
