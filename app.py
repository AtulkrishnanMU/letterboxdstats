import requests
from bs4 import BeautifulSoup
import streamlit as st
import re
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import plotly.express as px

import sqlite3
from imdb import IMDb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Connect to SQLite database
conn = sqlite3.connect('movies.db')
c = conn.cursor()

# Create table to store movie details
c.execute('''CREATE TABLE IF NOT EXISTS movies
             (username CHAR(50), year INTEGER, title TEXT, director TEXT, country TEXT, language TEXT, runtime INTEGER, genre TEXT, cast TEXT)''')

# Commit changes and close connection
conn.commit()

def get_user_stats(username):
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()

    # Calculate total runtime in hours for the given username
    c.execute("SELECT SUM(runtime) FROM movies WHERE username = ?", (username,))
    total_runtime_minutes = c.fetchone()[0]
    if total_runtime_minutes:
        total_runtime_hours = total_runtime_minutes / 60
        tot_hours = f"{total_runtime_hours:.2f} hours"
    else:
        tot_hours = "No movies found for the user"

    # Calculate total number of distinct directors for the given username
    c.execute("SELECT COUNT(DISTINCT director) FROM movies WHERE username = ?", (username,))
    tot_dirs = c.fetchone()[0]

    # Calculate total number of distinct countries for the given username
    c.execute("SELECT COUNT(DISTINCT country) FROM movies WHERE username = ?", (username,))
    tot_countries = c.fetchone()[0]

    conn.close()

    return tot_hours, tot_dirs, tot_countries

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
    base_url = f"https://letterboxd.com/{username}/films/by/date-earliest/"
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

def fetch_movie_details(username, movie_titles, stop_flag=0):
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
        if stop_flag==1:
            #st.write(f"{entry_count} movies imported till now")
            break
        else:
          try:
            movie = ia.search_movie(title)[0]
            ia.update(movie)

            year = movie.get('year', '')
            director = ', '.join([person['name'] for person in movie.get('directors', [])])
            country = movie.get('countries', [])[0] if movie.get('countries') else ''
            language = movie.get('languages', [])[0] if movie.get('languages') else ''
            runtime = movie.get('runtimes', [])[0] if movie.get('runtimes', []) else None
            genre = ', '.join(movie.get('genres', []))
            cast = ', '.join([person['name'] for person in movie.get('cast', [])])

            # Assuming you have defined progress_bar elsewhere
            progress_bar.progress((i + 1) / total_films)

            c.execute("INSERT INTO movies (username, year, title, director, country, language, runtime, genre, cast) VALUES (?,?,?,?,?,?,?,?,?)",
                      (username, year, title, director, country, language, runtime, genre, cast))

            conn.commit()

            i += 1
          except Exception as e:
            print(f"Error fetching details for '{title}': {e}")

    conn.close()

def count_genre_entries(username):
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()

    # Define genre names
    genre_names = ["Action", "Adventure", "Animation", "Biography", "Comedy", "Crime", "Documentary", "Drama",
                   "Family", "Fantasy", "Film-Noir", "History", "Horror", "Music", "Musical", "Mystery", 
                   "Romance", "Sci-Fi", "Short", "Sport", "Thriller", "War", "Western"]

    # Initialize a dictionary to store counts for each genre
    genre_counts = {}

    # Count the number of entries for each genre containing the specified genre name
    for genre in genre_names:
        c.execute("SELECT COUNT(*) FROM movies WHERE username = ? AND genre LIKE ?", (username, f"%{genre}%"))
        count = c.fetchone()[0]
        genre_counts[genre] = count

    conn.close()

    return genre_counts

def get_movie_statistics():
  
    # Fetch total hours watched
    c.execute("SELECT SUM(runtime) FROM movies")
    total_minutes = c.fetchone()[0]
    total_hours = total_minutes / 60

    # Fetch number of distinct directors watched
    c.execute("SELECT COUNT(DISTINCT director) FROM movies")
    distinct_directors = c.fetchone()[0]

    # Fetch number of distinct countries watched
    c.execute("SELECT COUNT(DISTINCT country) FROM movies")
    distinct_countries = c.fetchone()[0]

    # Fetch number of distinct languages watched
    c.execute("SELECT COUNT(DISTINCT language) FROM movies")
    distinct_languages = c.fetchone()[0]

    # Close the connection
    conn.close()

    # Return the results
    return total_hours, distinct_directors, distinct_countries, distinct_languages

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
                #if bio_text !="":
                    #st.write(f"Bio: {bio_text}")
            
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

    stop_flag = st.button("Stop for now")

    fetch_movie_details(username, movie_titles, stop_flag)

    progress_bar.progress(100)

    if stop_flag:
      c.execute("SELECT COUNT(*) FROM movies WHERE username = ?", (username,))
      entry_count = c.fetchone()[0]
      st.text(f"{entry_count} movies imported now")
      #st.script("document.querySelector('#stop_button').disabled = true;")

    # Get top categories
    total_hours, distinct_directors, distinct_countries, distinct_languages = get_movie_statistics()

    st.markdown(f"**Total hours watched:** <span style='font-size: 24px;'>{total_hours}</span>", unsafe_allow_html=True)
    st.markdown(f"**Number of distinct directors watched:** <span style='font-size: 24px;'>{distinct_directors}</span>", unsafe_allow_html=True)
    st.markdown(f"**Number of distinct countries watched:** <span style='font-size: 24px;'>{distinct_countries}</span>", unsafe_allow_html=True)
    st.markdown(f"**Number of distinct languages watched:** <span style='font-size: 24px;'>{distinct_languages}</span>", unsafe_allow_html=True)

    # Display top genres bar graph
    genre_counts = count_genre_entries(username)

    sorted_genre_counts = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Create a DataFrame from the sorted genre counts
    df_genre_counts = pd.DataFrame(sorted_genre_counts, columns=['Genre', 'Count'])
    
    # Add some style to the table
    st.markdown("<style> table td:nth-child(2) { text-align: center; } </style>", unsafe_allow_html=True)
    st.markdown("<style> table { font-size: 16px; } </style>", unsafe_allow_html=True)
    
    # Display top genres in a styled table without index
    st.markdown("## Top 10 Genre Distribution")
    st.write("Here are the top 10 genres and their respective counts:")
    st.table(df_genre_counts.set_index('Genre').style.set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#f7f7f9'), ('color', 'black'), ('font-weight', 'bold')]},
        {'selector': 'td', 'props': [('background-color', 'white'), ('color', 'black')]}
    ]))
  
    '''
    # Display top countries bar graph
    st.subheader("Top 10 Countries Watched:")
    countries = [country for country, _ in top_countries]
    num_films_country = [num_films for _, num_films in top_countries]
    fig_country = px.bar(x=num_films_country, y=countries, orientation='h', labels={'x':'Number of Films', 'y':'Country'})
    st.plotly_chart(fig_country)

    # Display top languages bar graph
    st.subheader("Top 10 Languages Watched:")
    languages = [language for language, _ in top_languages]
    num_films_language = [num_films for _, num_films in top_languages]
    fig_language = px.bar(x=num_films_language, y=languages, orientation='h', labels={'x':'Number of Films', 'y':'Language'})
    st.plotly_chart(fig_language)
    '''





    
