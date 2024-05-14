import requests
from bs4 import BeautifulSoup
import streamlit as st

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
        film_posters = films_container.find_all('div', class_='poster-container')
        for poster in film_posters:
            film_name = poster.find('div', class_='film-poster')['data-film-slug']
            film_link = f"https://letterboxd.com/film/{film_name}/"
            favorite_films.append((film_name, film_link))
    
    return name, bio, image_url, favorite_films

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
    for film_name, film_link in favorite_films:
        st.markdown(f"[{film_name}]({film_link})")
