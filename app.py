import requests
from bs4 import BeautifulSoup
import streamlit as st
import re
from PIL import Image, ImageDraw
import requests
from io import BytesIO

import sqlite3
from imdb import IMDb

# Connect to SQLite database
conn = sqlite3.connect('movies.db')
c = conn.cursor()

# Create table to store movie details
c.execute('''CREATE TABLE IF NOT EXISTS movies
             (username CHAR(50), title TEXT, director TEXT, country TEXT, language TEXT, runtime INTEGER, genre TEXT, cast TEXT)''')

# Commit changes and close connection
conn.commit()

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

def extract_movies(url):
    film_slugs = []
    movie_info = []
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    movie_containers = soup.find_all('li', class_='poster-container')
    #print(movie_containers)
    
    # Loop through each movie container
    for container in movie_containers:
        # Find the div element with class 'poster' inside the container
        div_element = container.find('div', class_='poster')
        # Check if the div_element exists and has the 'data-film-slug' attribute
        if div_element and 'data-film-slug' in div_element.attrs:
            # Extract the value of the 'data-film-slug' attribute and append it to the list
            film_slugs.append(div_element['data-film-slug'])

    # Print the list of film slugs
    return film_slugs

def extract_all_movies(username):
    base_url = f"https://letterboxd.com/{username}/films/"
    all_movies = []
    page_num = 1
    while True:
        url = f"{base_url}page/{page_num}/"
        #print(url)
        movies = extract_movies(url)
        if not movies:
            break
        all_movies.extend(movies)
        page_num += 1
    
    return all_movies

def fetch_movie_details(username, movie_titles):
    ia = IMDb()

    conn = sqlite3.connect('movies.db')
    c = conn.cursor()

    # Check if the username already exists in the table
    c.execute("SELECT title FROM movies WHERE username = ? ORDER BY ROWID DESC LIMIT 1", (username,))
    last_movie_title = c.fetchone()
    
    if last_movie_title:
        last_movie_title = last_movie_title[0]
        try:
            last_movie_index = movie_titles.index(last_movie_title)
            movie_titles = movie_titles[last_movie_index + 1:]
        except ValueError:
            # If last movie not found in movie_titles, insert all movies
            pass

    total_films = len(movie_titles)
    i = 0

    for title in movie_titles:
        try:
            movie = ia.search_movie(title)[0]
            ia.update(movie)

            director = ', '.join([person['name'] for person in movie.get('directors', [])])
            country = ', '.join(movie.get('countries', []))
            language = ', '.join(movie.get('languages', []))
            runtime = movie.get('runtimes', [])[0] if movie.get('runtimes', []) else None
            genre = ', '.join(movie.get('genres', []))
            cast = ', '.join([person['name'] for person in movie.get('cast', [])])

            # Assuming you have defined progress_bar elsewhere
            progress_bar.progress((i + 1) / total_films)

            c.execute("INSERT INTO movies (username, title, director, country, language, runtime, genre, cast) VALUES (?,?,?,?,?,?,?,?)",
                      (username, title, director, country, language, runtime, genre, cast))

            conn.commit()

            i += 1
        except Exception as e:
            print(f"Error fetching details for '{title}': {e}")

    conn.close()

# User input for username
username = st.text_input("Enter your Letterboxd username:")

if username:
    # Scraping the profile
    name, bio, image_url, favorite_films = scrape_profile(username)

    # Extracting first sentence, number of films watched, and bio
    first_sentence = bio.split('.')[0] + '.'
    films_watched = re.search(r'(\d{1,3}(,\d{3})*)(\.\d+)?', bio).group()
    total_films = int(films_watched.replace(',', ''))
    try:
        bio_text = bio.split('Bio: ')[1].strip()
    except:
        bio_text = ""

    # Displaying the details using Streamlit
    # st.title(name)
    st.markdown("<h1 style='text-align: center;'>{}</h1>".format(name), unsafe_allow_html=True)

    if image_url:
        try:
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))

            # Resize the image to desired dimensions
            new_width = 200  # Adjust the width as needed
            new_height = 200  # Adjust the height as needed
            img_resized = img.resize((new_width, new_height))

            # Mask the resized image to a circle
            img_circle = mask_to_circle(img_resized)

            # Create a layout with two columns
            col1, col2 = st.columns([1, 3])

            # Display the circular image in the first column
            with col1:
                st.image(img_circle, width=150)

            # Display the bio in the second column
            with col2:
                st.markdown(f"**{first_sentence}**")
                st.write(f"Films watched: **{films_watched}**")
                if bio_text !="":
                    st.write(f"Bio: {bio_text}")
            
        except Exception as e:
            st.error(str(e))
    
    #st.write(bio)
    
    st.subheader("Favorite Films:")
    poster_images = []
    try:
      film_names_with_year = bio.split("Favorites: ")[1].split(".")[0].split(", ")
      for i, (_, film_link) in enumerate(favorite_films):
          movie_image_url = get_movie_details(film_link)
          if movie_image_url:
              poster_images.append(movie_image_url)
      
      # Displaying poster images
      if poster_images:
          st.image(poster_images, caption=film_names_with_year, width=150)
    except:
        st.write("No favourite films")

    all_movies = extract_all_movies(username)

    # List of movie titles
    movie_titles = all_movies

    progress_bar = st.progress(0)
    
    # Fetch and store movie details
    fetch_movie_details(username, movie_titles)

    



    
