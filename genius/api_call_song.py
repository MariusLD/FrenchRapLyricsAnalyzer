import requests
import json
import api_key
import re
import os
import sys


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
        with open('genius/artistsJSON/' + name.replace(" ", "_") + '.json', 'w') as f:
            artistPage = requestFormat("get", 'artists/' + str(id) + '/songs')
            json.dump(artistPage.json(), f, indent=4, separators=(',', ': '))