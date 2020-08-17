import time

import pytest
import recommender
import numpy as np
import json
from scipy.spatial import distance
import mpd_connector
import termcolor
import logging
import TFIDF_recommender


def main():
    recommender_object = recommender.Recommender()
    """
    recommender_object.played_songs_session = [
        {'title': 'People Get Ready', 'artist': 'One Love', 'genre': 'Reggae'},
        {'title': 'Too Long / Steam Machine', 'artist': 'Daft Punk',
         'genre': 'Electronica'},
        {'title': 'Thing Called Love', 'artist': 'Land Of Giants',
         'genre': 'Alternative'}]
    """

    test_updating_user_information(recommender_object.user_controller)
    print("Recommend a song:")
    print(recommender_object.recommend_song())
    print("___")
    test_genre_recommendation(recommender_object, "Reggae")
    test_mood_recommendation_complete(recommender_object)
    #print(recommender_object.user_controller.get_percentages_genre_or_artist("genre"))
    #print(recommender_object.user_controller.get_percentages_genre_or_artist("artist"))
    # print(recommender_object.choose_recommended_song())
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

def test_tfidf():
    TFIDF_recommender.TFIDFInitializer()
    tfidf = TFIDF_recommender.TFIDF()
    tfidf.update_user_vector("Thing Called Love")
    tfidf.update_user_vector("Flow (feat. Mr. Woodnote & Flower Fairy)")
    tfidf.update_user_vector("She Used To Love Me A Lot")
    tfidf.update_user_vector("People Get Ready")
    tfidf.update_user_vector("Grind")
    tfidf.update_user_vector("Too Long / Steam Machine")
    print(tfidf.rank_by_cosine_similiarity())

def test_updating_user_information(user_controller):
    currently_played_song = {"title": "Grind", "artist": "Tangerine Dream", "genre": "Testgenre"}
    currently_played_song2 = {"title": "People Get Ready", "artist": "One Love", "genre": "Raggea"}
    currently_played_song3 = {"title": "She Used To Love Me A Lot", "artist": "Johnny Cash", "genre": "Country"}
    currently_played_song4 = {"title": "Thing Called Love", "artist": "Land Of Giants", "genre": "Alternative"}
    user_controller.update_preferences(currently_played_song)
    user_controller.update_preferences(currently_played_song2)
    user_controller.update_preferences(currently_played_song3)
    user_controller.update_preferences(currently_played_song4)
    user_controller.serialize_stats_all_time()


def test_session_weighting(number_session):
    result = -1 / (1 + np.math.exp(0.8 * number_session - 2)) + 0.9
    print(result)


def test_mood_recommendation_complete(recommender_object):
    def test_mood_recommendation(mood):
        print("recommending", mood, "songs:")
        print(recommender_object.recommend_song_mood(mood))
        print("___")

    test_mood_recommendation("positive")
    test_mood_recommendation("negative")
    #test_mood_recommendation("angry")
    #test_mood_recommendation("invalid_input")


def test_genre_recommendation(recommender_object, genre):
    print("Recommending songs of genre:", genre)
    print(recommender_object.recommend_song_genre(genre))
    print("___")


if __name__ == '__main__':
    main()
