import configparser

config = configparser.ConfigParser()
config.read("config_recommender.ini")


#[SPOTIFY]
CLIENT_ID = config.get("SPOTIFY", "CLIENT_ID")
CLIENT_SECRET = config.get("SPOTIFY", "CLIENT_SECRET")
REDIRECT_URI = config.get("SPOTIFY", "REDIRECT_URI")
REFRESH_TOKEN = config.get("SPOTIFY", "REFRESH_TOKEN")

#[MPD]
MPD_IP = config.get("MPD", "MPD_IP")
MPD_PORT = config.getint("MPD", "MPD_PORT")

#SAVE_PATH: Since these values should not be set by the user, they are set statically here
PATH_SONG_DATA = "spotifyRecommender/song_tags.json"
PATH_RELATED_ARTISTS = "spotifyRecommender/related_artists.json"
PATH_USER_DATA = "spotifyRecommender/user_data.json"
#TF-IDF
PATH_SONG_VECTORS = "tfidf/tfidf_data.json"
PATH_USER_VECTOR = "tfidf/tfidf_user_vector"