import requests
import numpy as np
from bs4 import BeautifulSoup
import re

# Get content from the "Rappeur Français" Wikipedia web page
url = "https://fr.wikipedia.org/wiki/Cat%C3%A9gorie:Rappeur_fran%C3%A7ais"
response = requests.get(url)
content = response.content

# We use BeautifulSoup to analyze the content
soup = BeautifulSoup(content, "html.parser")

# We are looking for the list of all rappers' name, they are actually listed in div mw-category
rappers = []
for element in soup.find_all("div", class_="mw-category"):
    for li in element.find_all("li"):
        rappers.append(re.sub(r'\([^)]*\)', '', li.text).strip())
rappers.pop(0)

# We write the data in rappers.txt
np.savetxt("beautifulsoup/rappers.txt", rappers, delimiter=" ", newline = "\n", fmt="%s")