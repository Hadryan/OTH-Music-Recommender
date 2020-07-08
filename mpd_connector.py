from mpd import MPDClient

client = MPDClient()
client.timeout = 10
client.idletimeout = None
client.connect("localhost", 6600)
print(client.mpd_version)
print(client.list("genre"))
print(client.find("any", "Kosmos"))
print(client.listfiles("Lieder_HighResolutionAudio"))
#print(client.tagtypes())
print(client.listallinfo("Lieder_HighResolutionAudio"))
client.close()
client.disconnect()