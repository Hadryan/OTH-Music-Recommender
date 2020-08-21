import json
from operator import itemgetter
import logging
import math
import os.path
import numpy as np
import nltk

import mpd_connector
import config_project


class TFIDF:
    def __init__(self):
        if not os.path.exists(config_project.PATH_SONG_VECTORS):
            TFIDFInitializer()
        self.song_vectors = self.read_vectors_from_json(config_project.PATH_SONG_VECTORS)
        self.user_vector = np.zeros(len(self.song_vectors[0][1]))
        try:
            with open(config_project.PATH_USER_VECTOR, "r") as json_file:
                self.user_vector = np.array(json.load(json_file))
        except FileNotFoundError:
            logging.info("No user profile for TFIDF recommender found!")

    @staticmethod
    def update_song_vectors():
        """Update the song vectors. This should be run, once you update your mpd library"""
        TFIDFInitializer()

    def update_user_vector(self, song_title):
        song_obj = next((item for item in self.song_vectors if item[0] == song_title), None)
        if not song_obj:
            print("No matching song found. Please update your tf-idf vectors.")
            return
        else:
            self.user_vector += song_obj[1]
        # serialize the user vector after every new addition
        self.serialize_user_vector()

    def serialize_user_vector(self):
        with open(config_project.PATH_USER_VECTOR, "w") as file_obj:
            json.dump(self.user_vector.tolist(), file_obj)

    def rank_by_cosine_similarity(self):
        recommend_list = []
        for song in self.song_vectors:
            similarity = np.dot(self.user_vector, song[1]) / (
                    np.linalg.norm(self.user_vector) * np.linalg.norm(song[1]))
            recommend_list.append({"title": song[0], "rating": similarity})
        return sorted(recommend_list, key=itemgetter("rating"), reverse=True)

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


class TFIDFInitializer:
    """
    This class prepares everything for the TF-IDF recommender. Just create a object of the class for all necessary steps.
    No need to call any methods.
    """

    def __init__(self):
        self.song_list = mpd_connector.MpdConnector(config_project.MPD_IP, config_project.MPD_PORT).get_all_songs()
        nltk.download('punkt')
        nltk.download("wordnet")
        self.initialize()

    def initialize(self):
        """
        initialize the tf-idf recommender.
        """
        new_song_list = self.remove_punctuation(self.join_song_data())
        token_list = self.tokenize(new_song_list)
        token_list_lemmatized = self.lemmanization(token_list)
        list_with_vectors = self.calculate_tfidf(token_list_lemmatized)
        self.vectors_to_json(list_with_vectors, config_project.PATH_SONG_VECTORS)

    def join_song_data(self):
        """Joins title. album name, year and interpreter to a single string"""
        joined_song_list = []
        for song_entry in self.song_list:
            merged_entry = song_entry["title"] + " " + song_entry["artist"].replace(" ", "") + " " + song_entry[
                "album"].replace(" ", "") + " " + song_entry["date"] + " " + song_entry["genre"].replace(" ", "")

            joined_song_list.append({"title": song_entry["title"], "body": merged_entry})
        return joined_song_list

    def remove_punctuation(self, joined_song_list):
        """
        Remove the punctuation and call lower() on the new title
        :param song_list: list of dicts with ["title"] as the relevant key
        """
        punctuation_to_remove = [",", ".", "(", ")", "[", "]", "!", "?", "\\", "/", "\"", "+", "*", "&", "|", "'", "-",
                                 ":"]
        new_song_list = []
        for song_entry in joined_song_list:
            for punctuation in punctuation_to_remove:
                song_entry["body"] = str(song_entry["body"]).replace(punctuation, "")
            new_song_list.append({"title_original": song_entry["title"], "body": song_entry["body"].lower()})
        return new_song_list

    def tokenize(self, song_list):
        """
        Splits the title into tokens and removes single letters
        :param: song_list: Returned by remove_punctuation()
        """
        token_list = []
        for song in song_list:
            tokens = nltk.word_tokenize(song["body"])
            tokens = [x for x in tokens if len(x) > 1]  # Remove single letters
            token_list.append({"title": song["title_original"], "tokens": tokens})
        return token_list

    def lemmanization(self, token_list):
        """
        lemmatizes the tokens. This means reducing words to their base forms,
        e.g. houses -> house or ran -> running
        :param: token_list: returned from tokenize()
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
        :return: returns list of dicts with the original title and the tf-idf values as a vector for each song
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
                # insert tf-idf at index
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
            json.dump(serializable_list, file_obj, indent=4)


