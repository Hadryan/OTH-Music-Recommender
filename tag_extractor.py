import tekore as tk
import parse_songnames

client_id = "08fce4b3fb2144838c7f65133d289fbc"
client_secret = "9011cc6827684eb783288bd04147140b"
redirect_uri = "http://localhost:8888"
refresh_token = "AQD2gsLOa6g984Kvt62WR2rT2rqJVzHIEN7GZWq23915TiKQQNpBKSQMTqoow11IoWRst3mBVbyh2GUKLrB6Us7AhNl25KWozaJpGIi2-WkUqUloiKmBsNTEG0da7b4wOcc"


def main():
    spotify = init()
    get_spotify_ids("songList.txt", spotify)

def init():
    """
    Initialize + authorize
    :return: spotify object on which api methods can be called
    """
    cred = tk.RefreshingCredentials(client_id, client_secret, redirect_uri)
    app_token = cred.request_client_token()
    user_token = cred.refresh_user_token(refresh_token)
    sender = tk.RetryingSender(sender=tk.CachingSender())
    spotify = tk.Spotify(user_token, max_limits_on=True, sender=sender)
    return spotify


def get_spotify_ids(path_songlist, spotify):
    track_list = parse_songnames.parse_songlist(path_songlist)
    print(track_list)
    spotify_id_list = []
    error_list = []
    for single_track_info in track_list:
        track_paging_object, = spotify.search(single_track_info[0] + " " + single_track_info[1], limit=1)
        if len(track_paging_object.items) != 0:
            spotify_id_list.append((single_track_info, track_paging_object.items[0].id))
        else:
            error_list.append(single_track_info)

#    print(spotify_id_list)
    print("correct:", len(spotify_id_list))
    print("false:", len(error_list))
 #   for error in error_list:
  #      print(error)

  #try getting more results by omitting the interpreter
    for single_track_info in error_list:
        track_paging_object, = spotify.search(single_track_info[1], limit=1)
        if len(track_paging_object.items) != 0:
            spotify_id_list.append((single_track_info, track_paging_object.items[0].id))
            error_list.remove(single_track_info)
    print("After second iteration:")
    print("correct:", len(spotify_id_list))
    print("false:", len(error_list))
    for error in error_list:
        print(error)


if __name__ == '__main__':
    main()
