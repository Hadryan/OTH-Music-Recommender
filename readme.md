## Content-based Recommender System

This Repository was created within the context of bachelor thesis @ [Ostbayerische Technische Hochschule Regensburg](https://www.oth-regensburg.de/)

This repository is intended to be integrated into a MPD client and does not support playback in itself.

2 Recommender Systems:
* Tf-idf-based Recommender System
* Content-Based Recommender System using the spotify API
 
### Prerequisites
* Python 3.5 or higher
* Running MPD Server
* Media library of the MPD Server must have complete metadata. Genre, Title and Artist are vital for this programm to work.  Alternative you have to tag your music database with a software like https://picard.musicbrainz.org/. Download and follow the instructions!

### Install
1. Clone this repository
1. CD into OTH-Music-Recommender
2. Check that MPD is running
3. Check if the IP and Port of your MPD server are correctly listed in config_recommender.ini, outherwise chance those values accordingly.
4. run "python setup.py install". If not using a virutal Environment this may require Root access. In that case use: "sudo python setup.py install"

Run Test_recommender.py for a full test of all features. Run it with 

    

