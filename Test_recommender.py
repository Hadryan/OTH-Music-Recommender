from SpotifyRecommender import recommender, tag_extractor
import numpy as np
from TfidfRecommender import TFIDF_recommender


def main():
    test_complete()
    """

    test_genre_recommendation(recommender_object, "Reggae")
    test_mood_recommendation_complete(recommender_object)
    # mpd_connector.test_mpd()
    # test_serialization()
    """


def test_complete():
    extract_song_tags()
    recommender_object = recommender.Recommender()
    test_updating_user_information(recommender_object.user_controller)
    recommend_list = recommender_object.recommend_song()
    recommend_list_positive = recommender_object.recommend_genre_or_mood("positive")
    recommend_list_negative = recommender_object.recommend_song_mood("negative")
    recommend_list_genre = recommender_object.recommend_genre_or_mood("Reggae")
    print()
    print("Recommend a song based on user profile:", recommend_list[0]["title"], "by", recommend_list[0]["interpreter"],
          "with a score of:", round(recommend_list[0]["score"], 4), "(perfect score would be 0).")
    print("All values:", recommend_list)
    print("_________")
    print("Recommend a\033[1m positive\033[0m song based on user profile:", recommend_list_positive[0]["title"], "by", recommend_list_positive[0]["interpreter"],
          "with a score of:", round(recommend_list_positive[0]["score"], 4), "(perfect score would be 0).")
    print("All values:", recommend_list_positive)
    print("_________")
    print("Recommend a\033[1m negative\033[0m song based on user profile:", recommend_list_negative[0]["title"], "by", recommend_list_negative[0]["interpreter"],
          "with a score of:", round(recommend_list_negative[0]["score"], 4), "(perfect score would be 0).")
    print("All values:", recommend_list_negative)
    print("_________")
    print("Recommend a\033[1m Reggae\033[0m song based on user profile:", recommend_list_genre[0]["title"], "by", recommend_list_genre[0]["interpreter"],
          "with a score of:", round(recommend_list_genre[0]["score"], 4), "(perfect score would be 0).")
    print("All values:", recommend_list_genre)
    print("_________")
    print("_________")
    print()
    print("Recommend a song using the\033[1m Tf-idf\033[0m Recommender:")
    test_tfidf()


def extract_song_tags():
    tag_extractor.TagExtractor()


def test_recommender_v1(recommender_object):
    print(recommender_object.get_eucl_distance_list(recommender_object.song_vectors,
                                                    recommender_object.user_controller.get_user_vector()))


def test_tfidf():
    tfidf = TFIDF_recommender.TFIDF()
    tfidf.update_user_vector("Thing Called Love")
    tfidf.update_user_vector("Flow (feat. Mr. Woodnote & Flower Fairy)")
    tfidf.update_user_vector("She Used To Love Me A Lot")
    tfidf.update_user_vector("People Get Ready")
    tfidf.update_user_vector("Grind")
    tfidf.update_user_vector("Too Long / Steam Machine")
    print(tfidf.rank_by_cosine_similarity())


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
    # test_mood_recommendation("angry")
    # test_mood_recommendation("invalid_input")


def test_genre_recommendation(recommender_object, genre):
    print("Recommending songs of genre:", genre)
    print(recommender_object.recommend_song_genre(genre))
    print("___")


if __name__ == '__main__':
    main()
