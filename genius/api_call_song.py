import requests
import json
import api_key
import re
import os
from bs4 import BeautifulSoup

# Function to send a request to Genius API, where the type of request is required and its endpoint 
def requestFormat(method, endpoint):
    auth_string = f"{api_key.access_token}"
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
    lyrics = html.select_one(
        'div[class^="lyrics"], div[class^="SongPage__Section"]'
    ).get_text(separator="\n")
    
    # We clean the lyrics as usual
    lyrics = re.sub(r'[\(\[].*?[\)\]]', '', lyrics)
    lyrics = os.linesep.join([s for s in lyrics.splitlines() if s])         
    return lyrics

def allLyricsToFile(name, urls):

    # For all the songs urls from the 'name' artist, we call the above function to get the lyrics and concatenate it into a new file
    f = open(working_directory + '/genius/artistsJSON/' + name + '/lyrics_' + name.lower() + '.txt', 'wb')
    for url in urls:
        lyrics = getLyrics(url)
        f.write(lyrics.encode("utf8"))
    f.close()

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
            artistPage = requestFormat("get", 'artists/' + str(id) + '/songs')
            json.dump(artistPage.json(), f, indent=4, separators=(',', ': '))

            urls=[]
            # We iterate through all songs from the artist
            for song in artistPage.json()['response']['songs']:
                urls.append(song['url'])
            allLyricsToFile(formatedName, urls)          