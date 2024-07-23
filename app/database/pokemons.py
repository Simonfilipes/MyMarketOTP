import requests
import tinydb
from bs4 import BeautifulSoup

def fetch_images_with_initiator(url: str, initiator_prefix: str = "Pokedex:"):
    # Request the content of the webpage
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to fetch the page. Status code: {response.status_code}")

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all image tags
    images = soup.find_all('img')

    filtered_images = []
    links = []
    # Filter images by initiator attribute
    for img in images:
      if "Min-" in img['alt']:
        img['alt'] = img['alt'].replace('Min-', "")
        # img['alt'] = img['alt'].replace('-', " ")
        img['alt'] = img['alt'].replace('.png', "")
        filtered_images.append(img['alt'])
        links.append(img['src'])

    return filtered_images, links

# Example usage
db = tinydb.TinyDB('./app/database/pokemons.json', indent = 4)
db.truncate()

url = 'https://wiki.otpokemon.com/index.php/Pokedex'  # Replace with the actual URL of the page
try:
    images, links = fetch_images_with_initiator(url)
    for c, img_src in enumerate(images):
        db.insert({
           "name": img_src,
           "link": "https://wiki.otpokemon.com" + links[c]
        })
except Exception as e:
    print(f"An error occurred: {e}")