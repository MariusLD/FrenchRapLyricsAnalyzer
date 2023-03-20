import requests
import numpy as np
from bs4 import BeautifulSoup
import re

rappers = []
# We are looking for the list of all rappers' name, they are actually listed in div mw-category
def artistsNames(soup):
    for element in soup.find_all("div", class_="mw-category"):
        for li in element.find_all("li"):
            rappers.append(re.sub(r'\([^)]*\)', '', li.text).strip())

# Get content from the "Rappeur Français" Wikipedia web page
url = "https://fr.wikipedia.org/wiki/Cat%C3%A9gorie:Rappeur_fran%C3%A7ais"
response = requests.get(url)
content = response.content

# We use BeautifulSoup to analyze the content
soupMainPage = BeautifulSoup(content, "html.parser")
artistsNames(soupMainPage)

# Find the button with the name "page suivante" and get the value of the "href" attribute 
button = soupMainPage.find('a', string='page suivante')
next_page_url = 'https://fr.wikipedia.org/' + button.get('href')   
response = requests.get(next_page_url)
content = response.content
soupNextPage = BeautifulSoup(content, "html.parser")
artistsNames(soupNextPage)

# We delete all occurences of some bruit
rappers = [i for i in rappers if i != 'Liste d\'artistes de hip-hop francophones']

# We write the data in rappers.txt
np.savetxt("beautifulsoup/rappers.txt", rappers, delimiter=" ", newline = "\n", fmt="%s")