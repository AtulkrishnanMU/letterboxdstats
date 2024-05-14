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
    
    return name, bio, image_url

# User input for username
username = st.text_input("Enter your Letterboxd username:")

if username:
    # Scraping the profile
    name, bio, image_url = scrape_profile(username)

    # Displaying the details using Streamlit
    st.title(name)
    st.image(image_url, caption='Profile Picture', use_column_width=True)
    st.write(bio)
