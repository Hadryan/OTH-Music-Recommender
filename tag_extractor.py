import tekore as tk

client_id = "08fce4b3fb2144838c7f65133d289fbc"
client_secret = "9011cc6827684eb783288bd04147140b"
redirect_uri = "http://localhost:8888"
refresh_token = "AQD2gsLOa6g984Kvt62WR2rT2rqJVzHIEN7GZWq23915TiKQQNpBKSQMTqoow11IoWRst3mBVbyh2GUKLrB6Us7AhNl25KWozaJpGIi2-WkUqUloiKmBsNTEG0da7b4wOcc"

# authorisation
cred = tk.RefreshingCredentials(client_id, client_secret, redirect_uri)
app_token = cred.request_client_token()
user_token = cred.refresh_user_token(refresh_token)
spotify = tk.Spotify(user_token)

# 1. Get List of songnames, will probably be some sort of with..open
# for now: testlist
testlist = ["House of the rising sun, five finger death punch", "Seven nation army, the white stripes",
            "Panzerkampf, Sabaton", "Die, Die, Crucify, Powerwolf", "iron man, black sabbath"]
spotify_id_list = []
for songname in testlist:
    track_paging_object, = spotify.search(songname, limit=1)
    spotify_id_list.append((songname, track_paging_object.items[0].id))


print(spotify_id_list)
