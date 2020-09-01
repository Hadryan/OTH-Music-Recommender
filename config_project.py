import configparser

config = configparser.ConfigParser()
config.read("config_recommender.ini")

#[SPOTIFY]
CLIENT_ID = config.get("SPOTIFY", "CLIENT_ID")
CLIENT_SECRET = config.get("SPOTIFY", "CLIENT_SECRET")

#[MPD]
MPD_IP = config.get("MPD", "MPD_IP")
MPD_PORT = config.getint("MPD", "MPD_PORT")

#SAVE_PATH: Since these values should not be set by the user, they are set statically here
PATH_SONG_DATA = "SpotifyRecommender/song_tags.json"
PATH_RELATED_ARTISTS = "SpotifyRecommender/related_artists.json"
PATH_USER_DATA = "SpotifyRecommender/user_data.json"
#TF-IDF
PATH_SONG_VECTORS = "TfidfRecommender/tfidf_data.json"
PATH_USER_VECTOR = "TfidfRecommender/tfidf_user_vector"