import pytest
import recommender
import numpy as np
import json
from scipy.spatial import distance
import mpd_connector

def main():
    recommender_object = recommender.Recommender()
    test_updating_user_information(recommender_object.user_controller)
    test_recommender_v1(recommender_object)
    #mpd_connector.test_mpd()
    #test_serialization()

def test_updating_user_information(user_controller):
    currently_played_song = {"title": "Grind", "artist": "Tangerine Dream", "genre": "Testgenre"}
    currently_played_song2 ={"title": "People Get Ready", "artist": "One Love","genre":"Raggea" }
    currently_played_song3 ={"title": "She Used To Love Me A Lot", "artist": "Johnny Cash","genre":"Country" }
    currently_played_song4 ={"title": " Thing Called Love", "artist": "Land of Giants","genre":"????" }
    user_controller.update_preferences(currently_played_song)
    user_controller.update_preferences(currently_played_song2)
    user_controller.update_preferences(currently_played_song3)
    user_controller.update_preferences(currently_played_song4)
    user_controller.serialize_stats_all_time()


def test_recommender_v1(recommender_object):
    print(recommender_object.recommend_song_v1())

def test_session_veighting(number_session):
    result = -1 / (1 + np.math.exp(0.8 * number_session - 2)) + 0.9
    print(result)


if __name__ == '__main__':
    main()