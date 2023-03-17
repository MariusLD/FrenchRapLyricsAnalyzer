# Run pip install -r requirements.txt in this directory
import requests
import json
import pandas as pd
import re
import os
from decouple import config
from bs4 import BeautifulSoup
from datetime import datetime 

# Function to send a request to Genius API, where the type of request is required and its endpoint 
def requestFormat(method, endpoint):
    auth_string = f"{config('access_token')}"
    headers = {
        'Accept': 'application/json',
        'Authorization' : f"Bearer {auth_string}"
    }
    url = 'https://api.genius.com/' + endpoint
    return requests.request(method, url, headers=headers, auth=None)

# A way to access to our text file from this script
working_directory = os.getcwd()
file_path = working_directory + '/beautifulsoup/rappers.txt'

# We retrieve all artists we are looking for from the file beautifulsoup/rappers.txt
file = open(file_path, 'r')
allNames = file.read().splitlines()

def getLyrics(url):

    # We collect the html object and then parse it with BeautifulSoup to get lyrics from the div class lyrics
    page_url = requests.get(url)
    html = BeautifulSoup(page_url.text, 'html.parser')
    lyrics_div = html.select_one(
        'div[class^="lyrics"], div[class^="SongPage__Section"]'
    )

    if lyrics_div is not None:
        lyrics = lyrics_div.get_text(separator="\n")
    
        # We clean the lyrics as usual  
        # We delete a section of the page that indicates how to write lyrics on Genius
        lyrics = re.sub(r'Embed.*?forum', '', lyrics, flags=re.DOTALL)

        # We delete every lines where we have "... Lyrics"
        lyrics = re.sub(r'(?i)^.*\bLyrics\b.*$', '', lyrics, flags=re.MULTILINE)
        
        # We delete a \n before every lines starting with "[Paroles ..."
        lyrics = re.sub(r'\[.*?\]', '', lyrics, flags=re.MULTILINE)

        lyrics = lyrics.replace("You might also like", '')
        
        # We delete every lines with a single digit in it 
        lines = lyrics.split('\n')
        lyrics = ''
        for line in lines:
            if not line.strip().isdigit():
                lyrics += line + '\n'
        return lyrics

    else:
        return None

start_time = datetime.now()

# Dataframe for processing
all_song_data = pd.DataFrame()

# We iterate through the array of names
for name in allNames:

    # We are making a request as we are typing in the search bar the name of the artist
    geniusSearch = requestFormat('get', 'search?q=' + name.replace(" ", "%20"))

    # This gives us a list of recommandations for our research
    pageToJSON = geniusSearch.json()['response']['hits']

    # We check if the first name dropping is the same as the one we typed, otherwise we consider that the artist is not referenced on the website
    if name==re.sub(r'\([^)]*\)', '', pageToJSON[0]['result']['artist_names']).strip():

        # Now we can get its id
        id = pageToJSON[0]['result']['primary_artist']['id']

        # For each artist found we create their own json with relevant infos such as all the songs they made 
        formatedName = name.replace(" ", "_")

        # We create a directory for the artist
        file_path = working_directory + '/genius/artistsJSON/' + formatedName
        isExist = os.path.exists(file_path)
        if not isExist:
            os.makedirs(file_path)

        # Pattern to replace songs titles
        rep = {"\xa0": "", " ": "_", "/": ""}
        rep = dict((re.escape(k), v) for k, v in rep.items()) 
        pattern = re.compile("|".join(rep.keys()))

        with open('genius/artistsJSON/'+ formatedName +'/' + formatedName + '.json', 'w') as f:
            count = 1
            artistPage = requestFormat("get", 'artists/' + str(id) + '/songs')

            # Loop until there is no more page to request for this artist
            while artistPage.json()['response']['next_page'] != None:
                artistPage = requestFormat("get", 'artists/' + str(id) + '/songs?page=' + str(count))
                json.dump(artistPage.json(), f, indent=4, separators=(',', ': '))
                
                # We iterate through all songs from the artist
                for song in artistPage.json()['response']['songs']:

                    # Check if the artists isn't a featured artist
                    if (id == song['primary_artist']['id']):
                        collected = getLyrics(song['url'])
                        if (collected != None):
                            lyrics = collected
                            songTitle = song['full_title'].replace('\u00a0', ' ')
                            print(songTitle)
                            date = song['release_date_components']
                            if (date != None):
                                year = song['release_date_components']['year']
                            else :
                                year = None
                            countF = sum([len(song['featured_artists'])])
                            row = {
                                "Year": year,
                                "Song Title": songTitle,
                                "Artist": formatedName,
                                "Lyrics": lyrics,
                                "Number of featured artists" : countF
                            }
                            new_df = pd.DataFrame([row])
                            all_song_data = pd.concat([all_song_data, new_df], axis=0, ignore_index=True)
                count += 1
            
all_song_data.to_csv('lyrics_df.csv', index=False, header=True)
end_time = datetime.now()
print("Total time to collect: {}".format(end_time - start_time))          