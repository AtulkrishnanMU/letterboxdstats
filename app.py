import requests
from bs4 import BeautifulSoup
import streamlit as st
import json

# Function to scrape the HTML and extract basic details
def scrape_profile(username):
    url = f"https://letterboxd.com/{username}/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extracting basic details
    name = soup.find('meta', property='og:title')['content']
    bio = soup.find('meta', property='og:description')['content']
    image_url = soup.find('meta', property='og:image')['content']
    
    return name, bio, image_url

# Function to scrape the HTML and extract movie details
def scrape_movie_details(movie_url):
    response = requests.get(movie_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the JSON-LD script containing movie details
    script_tag = soup.find('script', type='application/ld+json')
    if script_tag:
        # Extracting JSON data
        json_data = json.loads(script_tag.string)
        
        # Extracting movie title and poster URL
        title = json_data.get('name', 'Unknown Title')
        poster_url = json_data.get('image', '')
        
        return title, poster_url
    else:
        return None, None

# User input for username
username = st.text_input("Enter your Letterboxd username:")

if username:
    # Scraping the profile
    name, bio, image_url = scrape_profile(username)
    
    # Displaying profile details
    st.title(name)
    st.image(image_url, caption='Profile Picture', use_column_width=True)
    st.write(bio)
    
    st.write("---")
    st.write("Enter your favorite movie link(s):")
    movie_links_input = st.text_area("Paste movie link(s) here (one per line)")
    movie_links = movie_links_input.split('\n')

    for movie_link in movie_links:
        if movie_link.strip() != "":
            # Scraping movie details
            title, poster_url = scrape_movie_details(movie_link.strip())
            
            if title and poster_url:
                # Displaying the movie poster
                st.title(title)
                st.image(poster_url, caption=title, use_column_width=True)
            else:
                st.write(f"Movie details not found for link: {movie_link.strip()}")
