import TFIDF_recommender

TFIDF_recommender.TFIDFInitializer()
tfidf = TFIDF_recommender.TFIDF()
tfidf.update_user_vector("Thing Called Love")
tfidf.update_user_vector("Flow (feat. Mr. Woodnote & Flower Fairy)")
tfidf.update_user_vector("She Used To Love Me A Lot")
tfidf.update_user_vector("People Get Ready")
tfidf.update_user_vector("Grind")
tfidf.update_user_vector("Too Long / Steam Machine")
print(tfidf.rank_by_cosine_similiarity())
