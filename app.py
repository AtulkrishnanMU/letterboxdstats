import requests
from bs4 import BeautifulSoup
import streamlit as st
import re
from PIL import Image, ImageDraw
import requests
from io import BytesIO

def mask_to_circle(img):
    # Create a circular mask
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + img.size, fill=255)

    # Apply the circular mask to the image
    result = Image.new("RGBA", img.size, (255, 255, 255, 0))
    result.paste(img, (0, 0), mask)

    return result

# Function to scrape the HTML and extract basic details including favorite films and their links
def scrape_profile(username):
    url = f"https://letterboxd.com/{username}/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extracting basic details
    name = soup.find('meta', property='og:title')['content']
    bio = soup.find('meta', property='og:description')['content']
    image_url = soup.find('meta', property='og:image')['content']
    
    # Extracting favorite films and their links
    favorite_films = []
    films_container = soup.find('section', id='favourites')
    if films_container:
        film_posters = films_container.find_all('li', class_='poster-container')
        for poster in film_posters:
            film_name = poster.find('div', class_='film-poster')['data-film-slug']
            film_link = f"https://letterboxd.com/film/{film_name}/"
            favorite_films.append((film_name, film_link))
    
    return name, bio, image_url, favorite_films

# Function to get movie details from JSON data
def get_movie_details(movie_link):
    response = requests.get(movie_link)
    soup = BeautifulSoup(response.content, 'html.parser')
    script_tag = soup.find('script', type='application/ld+json')
    if script_tag:
        image_url = re.search(r'"image":"(.*?)"', str(script_tag)).group(1)
        return image_url
    else:
        return None

# User input for username
username = st.text_input("Enter your Letterboxd username:")

if username:
    # Scraping the profile
    name, bio, image_url, favorite_films = scrape_profile(username)

    # Displaying the details using Streamlit
    st.title(name)
    
    if image_url:
        try:
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))

            # Resize image to a smaller size
            img.thumbnail((200, 200))

            # Center-align the image
            st.image(img, use_column_width=True, caption="Original Image")

            # Mask the image to a circle
            img_circle = mask_to_circle(img)

            # Display the circular image
            st.image(img_circle, use_column_width=True, caption="Circular Image")

        except Exception as e:
            st.error(str(e))
    
    st.write(bio)
    
    st.subheader("Favorite Films:")
    poster_images = []
    film_names_with_year = bio.split("Favorites: ")[1].split(".")[0].split(", ")
    for i, (_, film_link) in enumerate(favorite_films):
        movie_image_url = get_movie_details(film_link)
        if movie_image_url:
            poster_images.append(movie_image_url)
    
    # Displaying poster images
    if poster_images:
        st.image(poster_images, caption=film_names_with_year, width=150)



    
