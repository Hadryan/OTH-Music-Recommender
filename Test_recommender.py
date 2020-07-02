import pytest
import recommender
import numpy as np
import json
from scipy.spatial import distance

def main():
    #test_vectors_temp()
    test_updating_user_informatiion()
    #test_serialization()

def test_updating_user_informatiion():
    currently_played_song = {"title": "Voyager", "artist": "Daft Punk", "genre": "Electro"}
    currently_played_song2 ={"title": "People Get Ready", "artist": "One Love","genre":"Raggea" }
    user_data = recommender.UserController("user_data.json")
    user_data.update_preferences(currently_played_song)
    user_data.update_preferences(currently_played_song2)
    user_data.serialize_stats_all_time()

def test_serialization():
    user_data = recommender.UserController("user_data.json")

def test_vectors_temp():
    test_vector = np.array([8.0, 3.0, 4.2, 9.8])
    # print(test_vector)
    test_vector2 = test_vector + np.array([1, 3, 5, 4])
    # print(test_vector)
    print(distance.euclidean([0,0,1], [1,0,0]))

if __name__ == '__main__':
    main()