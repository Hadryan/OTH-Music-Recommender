import pytest
import recommender
import numpy as np
import json

def main():
    test_updating_user_informatiion()
    #test_serialization()

def test_updating_user_informatiion():
    currently_played_song = {"title": "Voyager", "artist": "Daft Punk", "genre": "Electro"}
    user_data = recommender.UserData("user_data.json")
    user_data.update_preferences(currently_played_song)
    user_data.serialize_user_data()

def test_serialization():
    user_data = recommender.UserData("user_data.json")

def test_vectors_temp():
    test_vector = np.array([8.0, 3.0, 4.2, 9.8])
    # print(test_vector)
    test_vector = test_vector + np.array([1, 3, 5, 4])
    # print(test_vector)
    test_list = [3, 5, 7, 8]
    test_list = test_list / 2
    print(test_list)

if __name__ == '__main__':
    main()