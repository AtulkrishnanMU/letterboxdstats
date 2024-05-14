import requests
from bs4 import BeautifulSoup
import streamlit as st

# Function to scrape the HTML and extract basic details and favorite films
def scrape_profile(username):
    url = f"https://letterboxd.com/{username}/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extracting basic details
    name = soup.find('meta', property='og:title')['content']
    bio = soup.find('meta', property='og:description')['content']
    image_url = soup.find('meta', property='og:image')['content']
    
    # Extracting links of favorite films
    favorite_films = []
    films_section = soup.find('section', class_='films')
    if films_section:
        films = films_section.find_all('div', class_='poster film-poster')
        for film in films:
            film_link = film.find('a')['href']
            favorite_films.append(film_link)
    
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
    
    if favorite_films:
        st.header("Favorite Films")
        for film_link in favorite_films:
            st.markdown(f"[{film_link}]({film_link})")
    else:
        st.write("No favorite films found.")
