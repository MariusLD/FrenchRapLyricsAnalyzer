import requests
import json
import api_key
import re
import os

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

            # We iterate through all songs from the artist
            for song in artistPage.json()['response']['songs']:
                getMusic = requestFormat("get", "song/" + str(song['id']) + '&access_token=' + str(api_key.access_token))
                fileName = pattern.sub(lambda m: rep[re.escape(m.group(0))], song['full_title'].lower())
                if len(fileName) > 20:
                    fileName = fileName[0:34]
                with open('genius/artistsJSON/' + formatedName + '/' +  fileName + '.json', 'w') as f:
                    json.dump(getMusic.json(), f, indent=4, separators=(',', ': '))