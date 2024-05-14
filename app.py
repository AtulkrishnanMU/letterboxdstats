import requests
from bs4 import BeautifulSoup
import streamlit as st
import re

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
    st.image(image_url, caption='Profile Picture', use_column_width=True)
    st.write(bio)
    
    st.subheader("Favorite Films:")
    poster_images = []
    for film_name, film_link in favorite_films:
        movie_image_url = get_movie_details(film_link)
        if movie_image_url:
            poster_images.append((movie_image_url, film_name))
    
    # Displaying poster images
    if poster_images:
        for movie_image_url, film_name in poster_images:
            st.image(movie_image_url, caption=film_name, width=150)
