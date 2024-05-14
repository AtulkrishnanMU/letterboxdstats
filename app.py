import requests
from bs4 import BeautifulSoup
import streamlit as st

# Function to scrape the HTML and extract basic details
def scrape_profile(username):
    url = f"https://letterboxd.com/{username}/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extracting basic details
    name = soup.find('meta', property='og:title')['content']
    bio = soup.find('meta', property='og:description')['content']
    image_url = soup.find('meta', property='og:image')['content']
    
    # Extracting favorite films and their posters
    favorites_section = soup.find('section', class_='poster-list')
    favorites = []
    if favorites_section:
        posters = favorites_section.find_all('img', class_='image')
        for poster in posters:
            favorites.append(poster['src'])
    
    return name, bio, image_url, favorites

# User input for username
username = st.text_input("Enter your Letterboxd username:")

if username:
    # Scraping the profile
    name, bio, image_url, favorites = scrape_profile(username)

    # Displaying the details using Streamlit
    st.title(name)
    st.image(image_url, caption='Profile Picture', use_column_width=True)
    st.write(bio)
    
    st.header("Favorite Films:")
    if favorites:
        for favorite in favorites:
            st.image(favorite, caption='', use_column_width=True)
    else:
        st.write("No favorite films found.")
