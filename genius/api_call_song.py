# Run pip install -r requirements.txt in this directory
import requests
import json
import pandas as pd
import re
import os
from decouple import config
from bs4 import BeautifulSoup
from datetime import datetime 
from tqdm import tqdm

# Total number of API calls
total_calls = 0
# Keep track of a potential error with a call to the API
fetchLater = []

# Function to send a request to Genius API, where the type of request is required and its endpoint 
def requestFormat(method, endpoint):
    global total_calls
    total_calls += 1
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
    print(url)
    # We collect the html object and then parse it with BeautifulSoup to get lyrics from the div class lyrics
    page_url = requests.get(url)
    html = BeautifulSoup(page_url.text, 'html.parser')
    lyrics_div = html.select_one(
        'div[class^="lyrics"], div[class^="SongPage__Section"], div[class^="Lyrics__Container"]'
    )

    if lyrics_div is not None:
        lyrics = lyrics_div.get_text(separator="\n")
    
        # We clean the lyrics as usual  
        # We delete a section of the page that indicates how to write lyrics on Genius
        lyrics = re.sub(r'Embed.*?forum', '', lyrics, flags=re.DOTALL)

        # We delete every lines where we have "... Lyrics"
        lyrics = re.sub(r'(?i)^.*\bLyrics\b.*$', '', lyrics, flags=re.MULTILINE)
        
        # We delete a \n before every lines starting with "[Paroles ..."
        lyrics = re.sub(r'\[.*?\]', '', lyrics, flags=re.DOTALL)

        lyrics = lyrics.replace("You might also like", '')
        
        # We delete every lines with a single digit in it 
        lines = lyrics.split('\n')
        lyrics = ''
        for line in lines:
            if not line.strip().isdigit():
                lyrics += line + '\n'
        return lyrics
    else:
        print("No lyrics found for the previous url div name may be specific or the song is an instrumental")
        return None

start_time = datetime.now()

# Dataframe for processing
all_song_data = pd.DataFrame()

# We iterate through the array of names
for name in tqdm(allNames):
    try:
        # We are making a request as we are typing in the search bar the name of the artist
        geniusSearch = requestFormat('get', 'search?q=' + name.replace(" ", "%20"))

        # This gives us a list of recommandations for our research
        pageToJSON = geniusSearch.json()['response']['hits']
        
        if len(pageToJSON) > 0:
            # We iterate through the response to find the exact name as the search
            for searchOption in pageToJSON :
                # We check if the first name dropping is the same as the one we typed, otherwise we consider that the artist is not referenced on the website
                if name.lower()==re.sub(r'\([^)]*\)', '', searchOption['result']['artist_names']).strip().lower():
                    
                    # Now we can get its id
                    id = searchOption['result']['primary_artist']['id']

                    # For each artist found we create their own json with relevant infos such as all the songs they made 
                    formatedName = name.replace(" ", "_")
                    print("Collecting lyrics for: " + name + " with ID : " + str(id))

                    # We create a directory for the artist
                    file_path = working_directory + '/genius/artistsJSON/' + formatedName
                    isExist = os.path.exists(file_path)
                    if not isExist:
                        os.makedirs(file_path)

                    # Pattern to replace songs titles
                    rep = {"\xa0": "", " ": "_", "/": ""}
                    rep = dict((re.escape(k), v) for k, v in rep.items()) 
                    pattern = re.compile("|".join(rep.keys()))

                    count = 1
                    artistPage = requestFormat("get", 'artists/' + str(id) + '/songs')

                    # Loop until there is no more page to request for this artist
                    while artistPage.json()['response']['next_page'] != None:
                        with open('genius/artistsJSON/'+ formatedName +'/' + formatedName + str(count) + '.json', 'w') as f:
                            artistPage = requestFormat("get", 'artists/' + str(id) + '/songs?page=' + str(count))
                            json.dump(artistPage.json(), f, indent=4, separators=(',', ': '))
                            
                            # We iterate through all songs from the artist
                            for song in artistPage.json()['response']['songs']:
                            
                                # Check if the artists isn't a featured artist
                                if (id == song['primary_artist']['id']):
                                    collected = getLyrics(song['url'])
                                    if (collected != None):
                                        lyrics = collected
                                        songTitle = song['full_title'].replace('\u00a0', ' ').replace(' by ' + name, '')
                                        year = song['release_date_components']['year'] if song['release_date_components'] is not None else None
                                        countF = sum([len(song['featured_artists'])])
                                        pattern = r"\s*\([^)]*\)"
                                        # Remove the parentheses and everything inside them from a string
                                        def remove_parentheses(s):
                                            return re.sub(pattern, "", s)
                                        featured = None if not song['featured_artists'] else [remove_parentheses(artist['name']) for artist in song['featured_artists']]
                                        row = {
                                            "Year": year,
                                            "Song Title": songTitle,
                                            "Artist": formatedName,
                                            "Lyrics": lyrics,
                                            "Number of featured artists" : countF,
                                            "Featured artists" : featured
                                        }
                                        new_df = pd.DataFrame([row])
                                        all_song_data = pd.concat([all_song_data, new_df], axis=0, ignore_index=True)
                            count += 1
                    break
    except (requests.exceptions.RequestException, json.decoder.JSONDecodeError) as e:
        fetchLater.append(name)
        # Handle rare of errors from API response to avoid breaking the loop
        print(f"An error occurred while processing {name}: {e}")

all_song_data.to_csv('lyrics_df.csv', index=False, header=True)
end_time = datetime.now()
print("Number of API calls: {} Total time to collect: {}".format(total_calls, end_time - start_time))
print("Artists not found due to wrong API responses: {}".format(fetchLater))        