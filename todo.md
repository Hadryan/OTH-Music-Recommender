1. get refresh-token + save as static variable:
    user_token = tk.prompt_for_user_token(
        client_id,
        client_secret,
        redirect_uri,
        scope=tk.scope.every
    )
    print(user_token.refresh_token)

auch möglich nach isrc zu suchen (falls die mpd tags das hergeben)

nächste Schritte:
1. Kleine Testliste anlegen
2. extrahieren in liste aus dict, damit in json abgespeichert werden kann -> was performancemäßig am besten? DB/csv/json etc
3. immer in 100er chunks teilen
4. abfangen wenn api limit erreicht
5. mehrdimensionalen vektor bilden (wie man besten in python?)
6. wahrscheinlich reicht es diesen Vektor für jedes lied zu speichern (+ doc wie aufgebaut)

"""
If Web API returns status code 429, it means that you have sent too many requests.
When this happens, check the Retry-After header, where you will see a number displayed.
This is the number of seconds that you need to wait, before you try your request again.
"""

##RECOMMENDER:
* Serialization and deserialization done, not tested properly
* Created song vector Creation
* Created Update after song played
* [TO TEST] Created functions to return the percentage of genres and artists
* Created extra class to store user information

 ###TODO_General
 * in ersten Iteration genre und artist ignorieren, nur mit vektoren arbeiten [DONE]
 * probieren wie metadaten infos über mpd-schnittstelle kriegen[DONE]
 * Integration in speech processing (vmlt wichtiger als in anothrclient)
 
 

 ###TODO_concrete [DONE]
 choose_recommended_song() {Scoring functions: "statistical methods for recommender systems - 2.3"
 Method to weight the session -> z.B. einfach durchnschnitt bilden aus 6x session vector, 4x total vector
 

 ###Notes:
  - always check if not comparing to an empty vector (bc. init with [0,0,0]) before using vectors
  - nehme euklidische distanz statt cos, da damit infos verloren gehen würden, e.g. [1,1] und [0.2,0.2] gleicher winkel
  
  
TODO NEU: 
 - in tag_extractor mediapath rausnehmen und durch was allgemeines erstetzen
 - doc schreiben wie spotify referesh-token ersetzt werden kann  




