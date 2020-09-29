from SpotifyRecommender import recommender, tag_extractor
from TfidfRecommender import TFIDF_recommender
import sys
import math

"""This class is for testing purposes only. It is not required for any functionality of the recommender system"""


def main():
    if len(sys.argv) > 1:
        test_complete(True)
    else:
        test_complete(False)


def test_complete(with_extraction):
    if with_extraction:
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
    print("Top 10 songs:")
    beautify_list_printing(recommend_list, 10)
    print("_________")
    print("Recommend a\033[1m positive\033[0m song based on user profile:", recommend_list_positive[0]["title"], "by",
          recommend_list_positive[0]["interpreter"],
          "with a score of:", round(recommend_list_positive[0]["score"], 4), "(perfect score would be 0).")
    print("Top 10 songs:")
    beautify_list_printing(recommend_list_positive, 10)
    print("_________")
    print("Recommend a\033[1m negative\033[0m song based on user profile:", recommend_list_negative[0]["title"], "by",
          recommend_list_negative[0]["interpreter"],
          "with a score of:", round(recommend_list_negative[0]["score"], 4), "(perfect score would be 0).")
    print("Top 10 songs:")
    beautify_list_printing(recommend_list_negative, 10)
    print("_________")
    if recommend_list_genre:
        print("Recommend a\033[1m Reggae\033[0m song based on user profile:", recommend_list_genre[0]["title"], "by",
              recommend_list_genre[0]["interpreter"],
              "with a score of:", round(recommend_list_genre[0]["score"], 4), "(perfect score would be 0).")
        print("Top 10 songs:")
        beautify_list_printing(recommend_list_genre, 10)
    else:
        print("No songs of that genre in media library")
    print("=========")
    print("Recommend a song using the\033[1m Tf-idf\033[0m Recommender:")
    recommend_list_tfidf = test_tfidf()
    print(recommend_list_tfidf[0]["title"], "by", recommend_list_tfidf[0]["interpreter"], "with a score of:", recommend_list_tfidf[0]["rating"])

def extract_song_tags():
    tag_extractor.TagExtractor()


def test_recommender_v1(recommender_object):
    print(recommender_object.get_eucl_distance_list(recommender_object.song_vectors,
                                                    recommender_object.user_controller.get_user_vector()))


def test_tfidf():
    tfidf = TFIDF_recommender.TFIDF()
    #tfidf.update_user_vector("Longview")
    tfidf.update_user_vector("If Eternity Should Fail")
    tfidf.update_user_vector("Take the Power Back")
    tfidf.update_user_vector("Know Your Enemy")
    tfidf.update_user_vector("Kokain")
    tfidf.update_user_vector("Chewed Alive")

    return tfidf.rank_by_cosine_similarity()


def test_updating_user_information(user_controller):
    currently_played_song = {"title": "Riders on the Storm", "artist": "The Doors", "genre": "Rock"}
    currently_played_song2 = {"title": "Man for All Seasons", "artist": "Billy Idol", "genre": "Punk"}
    currently_played_song3 = {"title": "Don't You Think It's Come Our Time", "artist": "Johnny Cash",
                              "genre": "Country"}
    currently_played_song4 = {"title": "Time", "artist": "Pink Floyd", "genre": "Progressive Rock"}
    currently_played_song5 = {"title": "Parallel Universe", "artist": "Red Hot Chili Peppers", "genre": "Funk Rock"}
    user_controller.update_preferences(currently_played_song)
    user_controller.update_preferences(currently_played_song2)
    user_controller.update_preferences(currently_played_song3)
    user_controller.update_preferences(currently_played_song4)
    user_controller.update_preferences(currently_played_song5)
    user_controller.serialize_stats_all_time()


def test_session_weighting():
    y_values = []
    x_values = []
    for i in range(20):
        x_values.append(i)
        y_values.append(-1 / (1 + math.exp(0.8 * i - 2.19)) + 0.9)
        print(round(-1 / (1 + math.exp(0.8 * i - 2.19)) + 0.9, 2))
    plt.figure(figsize=(10, 5))
    plt.plot(x_values, y_values)
    plt.axis([0, 20, 0, 1])
    plt.xlabel("Anzahl Lieder in Session")
    plt.ylabel("Gewichtung")
    plt.title("Session Gewichtung")
    plt.savefig("weighting")
    plt.show()


def test_mood_recommendation_complete(recommender_object):
    def test_mood_recommendation(mood):
        print("recommending", mood, "songs:")
        print(recommender_object.recommend_song_mood(mood))
        print("___")

    test_mood_recommendation("positive")
    test_mood_recommendation("negative")
    test_mood_recommendation("invalid_input")


def test_genre_recommendation(recommender_object, genre):
    print("Recommending songs of genre:", genre)
    print(recommender_object.recommend_song_genre(genre))
    print("___")


def get_tempo_range():
    """Used to create a histogram of the BPM in the media library.
     To get absolute values first disable tempo scaling in tag_extractor"""

    tag_extractor.TagExtractor()
    recommender_object = recommender.Recommender()
    json_data = recommender_object.json_data
    tempo_list = []
    for song in json_data:
        tempo_list.append(song["audio_features"]["tempo"])
    plt.hist(tempo_list, bins=30)
    plt.title("BPM Verteilung")
    plt.xlabel("Beats per Minute (BPM)")
    plt.ylabel("Häufigkeit")
    plt.savefig("Verteilung BPM")


def beautify_list_printing(recommender_list, nbr_entries):
    for i in range(nbr_entries):
        print(recommender_list[i]["title"], "by", recommender_list[i]["interpreter"], "with a score of:",
              round(recommender_list[i]["score"], 4))


if __name__ == '__main__':
    main()
