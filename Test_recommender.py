import pytest
import recommender
import numpy as np
import json
from scipy.spatial import distance

def main():
    user_controller = recommender.UserController("user_data.json")
    test_updating_user_information(user_controller)
    test_recommender_v1(user_controller)

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


def test_recommender_v1(user_controller):
    print(recommender.recommend_song_v1(user_controller))


if __name__ == '__main__':
    main()