import tekore as tk

client_id = "08fce4b3fb2144838c7f65133d289fbc"
client_secret = "9011cc6827684eb783288bd04147140b"
redirect_uri = "http://localhost:8888"
refresh_token = "AQD2gsLOa6g984Kvt62WR2rT2rqJVzHIEN7GZWq23915TiKQQNpBKSQMTqoow11IoWRst3mBVbyh2GUKLrB6Us7AhNl25KWozaJpGIi2-WkUqUloiKmBsNTEG0da7b4wOcc"
user_code = "AQA30iT2Pps_Nep-pGcIqn7T8jM1MwZVXeMnsj_CrdFezyeSPqQcJGNo6lacRSMJ2q-KeapBLFCpd77fRVFD7HffeDCsE8nSZPm71sPt2eCMQwAIwCjJpJGEI8OIzRvGLCtEZuepscHPCnLbao8K7isiEpWAfkmx6OPcvXU7ShiZUgRzjd8G8HwjRHJOA55JpKIzoIigYWdd1fv0NMXXRQV9wwgIr2hjVxMZ2hvAvj4wSSVUIQ68JXFme48hu5rPG5immvrT1Uyw2iSLIaZHOWuUbl4XHgAztkwn8IASDjdgHxBoeoUpMYNoZbe8AWti7M4jm5fwOWcYLc_kkH6TT64QeO0SGatIzSnic_YJZCVBLC3tarll58RD4FuODN6-wfRhknn0DizoFwjUZ3nafdmkQQUlnUe2oK_vMbiJ_DYEFcOnviYUNnGePyhtZ_okZgAjR7tRJjnZduB1tfNIfC_GN3_MWCAZgeO2f0hbVnOn1Nu5nob6TJ9APq2j-GcVByXsGgycLywjUUTZ6w124AMXDCeIoerUO4j8oVPb5eASK4uhALW7RF9AwTHgWy8bedZCJu18-TRrLi0OAoVmOHodrpRgU22jWCNsUWe8TwJBr0imoYdAeUZsYpz7dPjFMbnrfCrRLvUXyLUe2_AqGj6fM44IaWp5PwInAw"

cred = tk.RefreshingCredentials(client_id, client_secret, redirect_uri)
app_token = cred.request_client_token()
user_token = cred.refresh_user_token(refresh_token)
spotify = tk.Spotify(user_token)


"""
album = spotify.album('3RBULTZJ97bvVzZLpxcB0j')
for track in album.tracks.items:
    print()
    print(track.track_number, track.name)

tracks = spotify.current_user_top_tracks(limit=10)
for track in tracks.items:
    print()
    print(track.name)


"""
tracks_without_artist, = spotify.search("house of the rising sun", limit = 1)
tracks, = spotify.search("house of the rising sun, Five finger death punch", types=("track",), limit = 1)
#spotify.playback_start_tracks(['4ZmX8elKMkH0MfniNi0Adu'])
print(tracks.items[0])
print(spotify.track_audio_features(tracks.items[0].id))