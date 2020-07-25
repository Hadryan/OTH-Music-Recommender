import json
from operator import itemgetter
import logging
import nltk
import math
import numpy as np
import \
    sklearn.metrics.pairwise  # Scikit-learn: Machine Learning in Python, Pedregosa et al., JMLR 12, pp. 2825-2830, 2011.
import mpd_connector

IP_MPD = "localhost"
PORT_MPD = "6600"
PATH_SONG_VECTORS = "data/tfidf_data.json"
PATH_USER_VECTOR = "data/tfidf_user_vector"


class TFIDF:
    def __init__(self):
        self.song_vectors = TFIDFInitializer.read_vectors_from_json(PATH_SONG_VECTORS)
        self.user_vector = np.zeros(len(self.song_vectors[0][1]))
        try:
            with open(PATH_USER_VECTOR, "r") as json_file:
                self.user_vector = np.array(json.load(json_file))
        except FileNotFoundError:
            logging.info("No user profile for TFIDF recommender found!")

    def update_user_vector(self, song_title):

        song_obj = next((item for item in self.song_vectors if item[0] == song_title), None)
        if not song_obj:
            print("No matching song found. Please update your tfidf vectors.")
            return
        else:
            self.user_vector += song_obj[1]
        # serialize the user vector after every new addition
        self.serialize_user_vector()

    def serialize_user_vector(self):
        with open(PATH_USER_VECTOR, "w") as file_obj:
            json.dump(self.user_vector.tolist(), file_obj)

    def rank_by_cosine_similiarity(self):
        recommend_list = []
        for song in self.song_vectors:
            similarity = np.dot(self.user_vector, song[1]) / (np.linalg.norm(self.user_vector) * np.linalg.norm(song[1]))
            #similarity = sklearn.metrics.pairwise.cosine_similarity(self.user_vector, song[1])
            recommend_list.append({"title": song[0], "rating": similarity})
        return sorted(recommend_list, key=itemgetter("rating"), reverse=True)


class TFIDFInitializer:
    """
    This class prepares everything for the TF-IDF recommender. Just create a object of the class for all necessary steps.
    No need to call any methods.
    """

    def __init__(self):
        # self.user_vector = np.array()
        self.title_list = mpd_connector.MpdConnector(IP_MPD, PORT_MPD).get_all_songs()
        nltk.download('punkt')
        nltk.download("wordnet")
        self.initialize()

    def initialize(self):
        """
        initialize the tf-idf recommender.
        :return:
        """
        new_song_list = self.remove_punctuation(self.title_list)
        token_list = self.tokenize(new_song_list)
        token_list_lemmatized = self.lemmanization(token_list)
        list_with_vectors = self.calculate_tfidf(token_list_lemmatized)
        self.vectors_to_json(list_with_vectors, "data/tfidf_data.json")

    def remove_punctuation(self, song_list):
        """
        Remove the punctation and call lower() on the new title
        :param song_list:
        """
        punctuation_to_remove = [",", ".", "(", ")", "[", "]", "!", "?", "\\", "/", "\"", "+", "*", "&", "|", "'", "-"]
        new_song_list = []
        for song_entry in song_list:
            song_title = song_entry["title"]
            for punctuation in punctuation_to_remove:
                song_title = str(song_title).replace(punctuation, "")
            new_song_list.append({"title_original": song_entry["title"], "title_modified": song_title.lower()})
        return new_song_list

    def tokenize(self, song_list):
        """
        Splits the title into tokens
        :return:
        """
        token_list = []
        for song in song_list:
            tokens = nltk.word_tokenize(song["title_modified"])
            token_list.append({"title": song["title_original"], "tokens": tokens})
        return token_list

    def lemmanization(self, token_list):
        """
        lemmatizes the tokens. This means reducing words to their base forms,
        e.g. houses -> house or ran -> running
        :param token_list:
        :return:
        """
        lemmatizer = nltk.stem.WordNetLemmatizer()
        for song in token_list:
            tokens_lemmatized = []
            for token in song["tokens"]:
                tokens_lemmatized.append(lemmatizer.lemmatize(token))
            song["tokens"] = tokens_lemmatized
        return token_list

    def calculate_tfidf(self, token_list):
        """
        calculates the TF-IDF value for every token in every song.
        Its calculated by the following formula:
        (nbr of term t in document / total nbr of terms in document) * log10(nbr documents / nbr docs with term t)
        :return:returns list of dicts with the original title and the tf-idf values as a vector for each song
        """
        total_occurences_term_dict = {}
        for song in token_list:
            token_dict = {}
            counted_tokens = []  # Terms that occur more than once per song are only counted once in total_occurences_term_dict
            for token in song["tokens"]:
                if token not in token_dict:
                    token_dict[token] = 1
                else:
                    token_dict[token] += 1
                if token not in counted_tokens:
                    if token not in total_occurences_term_dict:
                        total_occurences_term_dict[token] = 1
                    else:
                        total_occurences_term_dict[token] += 1

            song["token_dict"] = token_dict
            # song["count"] = len(song["tokens"])
        all_token_tuple_list = list(total_occurences_term_dict.items())
        for song in token_list:
            new_tfid_vector = np.zeros(len(all_token_tuple_list))
            for token in song["tokens"]:
                token_index = None
                for i in range(len(all_token_tuple_list)):
                    if token == all_token_tuple_list[i][0]:
                        token_index = i
                        break
                if token_index is None:
                    print("TOKEN NOT FOUND! ERROR")
                ##tfidf bei index einfügen
                tf = song["token_dict"][token] / len(song["tokens"])
                idf = math.log10(len(token_list) / total_occurences_term_dict[token])
                tf_idf = tf * idf
                new_tfid_vector[token_index] = tf_idf
            song["vector"] = new_tfid_vector
        return token_list

    @staticmethod
    def vectors_to_json(token_list, path_json):
        serializable_list = []
        for song in token_list:
            serializable_list.append([song["title"], song["vector"].tolist()])
        with open(path_json, "w") as file_obj:
            json.dump(serializable_list, file_obj)

    @staticmethod
    def read_vectors_from_json(path):
        """
        :param path: path to json file
        :return: returns [[title, np.array(vector)], ...]
        """
        with open(path, "r") as json_file:
            data = json.load(json_file)
        for song in data:
            song[1] = np.array(song[1])
        return data
