import pandas as pd
import sqlite3
from imdb import IMDb  # Make sure to have the IMDbPY package installed

# Initialize the IMDb API
ia = IMDb()

from bs4 import BeautifulSoup
import requests
import csv
import os

def convert_rating_to_integer(rating: str) -> int:
    # Define the star values
    star_values = {
        '★': 2,  # full star value
        '½': 1   # half star value
    }
    
    total_value = 0
    
    # Process each character in the rating string
    for char in rating:
        if char in star_values:
            total_value += star_values[char]
    
    # Adjust the output based on the rules provided
    if total_value == 1:  # ½
        return 1
    elif total_value == 2:  # ★
        return 2
    elif total_value == 3:  # ★½
        return 3
    elif total_value == 4:  # ★★
        return 4
    elif total_value == 5:  # ★★½
        return 5
    elif total_value == 6:  # ★★★
        return 6
    elif total_value == 7:  # ★★★½
        return 7
    elif total_value == 8:  # ★★★★
        return 8
    elif total_value == 9:  # ★★★★½
        return 9
    elif total_value == 10:  # ★★★★★
        return 10
    return 0  # Default return if nothing matches

def collect_and_save_user_movies(username):
    # CSV file path
    csv_file = 'user.csv'
    
    # Helper function to extract movies from a given page URL
    def extract_movies(url):
        film_data = []
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        movie_containers = soup.find_all('li', class_='poster-container')

        for container in movie_containers:
            # Movie name
            movie_name = container.find('img').get('alt') if container.find('img') else "Unknown"
            
            # Year and rating
            year_span = container.find('span', class_='year')
            year = year_span.text if year_span else "Unknown"
            rating_span = container.select_one('p.poster-viewingdata .rating')
            rating = convert_rating_to_integer(rating_span.text) if rating_span else None
            
            # Append movie data
            film_data.append((username, movie_name, year, rating))
        
        return film_data

    # Base URL for user movies
    base_url = f"https://letterboxd.com/{username}/films/by/date-earliest/"
    all_movies = []
    page_num = 1

    # Loop through paginated movie lists until no more movies are found
    while True:
        url = f"{base_url}page/{page_num}/"
        movies = extract_movies(url)
        if not movies:
            break
        all_movies.extend(movies)
        page_num += 1

    # Check existing entries in CSV to avoid duplicates
    existing_entries = set()
    if os.path.exists(csv_file):
        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                existing_entries.add((row[0], row[1], row[2], row[3]))

    # Write new entries to CSV
    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write header if the file is new
        if os.path.getsize(csv_file) == 0:
            writer.writerow(['Username', 'Movie Name', 'Year', 'Rating'])

        # Write movie data only if it does not exist
        for movie in all_movies:
            if movie not in existing_entries:
                writer.writerow(movie)

    print(f'Movie data for {username} has been saved to {csv_file}.')


def adjust_list(input_list):
    if len(input_list) > 5:
        return input_list[:5]
    else:
        return input_list + ['NULL'] * (5 - len(input_list))

# Function to get movie details from IMDb
def get_movie_details(movie_name):
    try:
        # Search for the movie
        movies = ia.search_movie(movie_name)

        if movies:
            movie = ia.get_movie(movies[0].movieID)

            # Extracting the required details
            director = ', '.join([person['name'] for person in movie.get('directors', [])])
            cast = [person['name'] for person in movie.get('cast', [])][:5]  # First 5 cast members
            cast += [''] * (5 - len(cast))  # Fill empty cast slots if less than 5
            duration = movie.get('runtime', [''])[0]

            # Get the year of release
            year = movie.get('year', '')

            # Get the first country, genre, and language
            countries = movie.get('countries', [])
            languages = movie.get('languages', [])
            genres = movie.get('genres', [])

            return {
                'year': year,
                'director': director,
                'cast': cast,
                'duration': duration,
                'country': countries[0] if countries else '',
                'genres': genres[:5],  # First 5 genres
                'language': languages[0] if languages else ''
            }
        else:
            return None  # If movie not found
    except Exception as e:
        print(f"Error retrieving movie details for {movie_name}: {e}")
        return None

# Function to create and populate the SQLite database
def create_and_populate_db(ratings_file, username, db_name='movies.db', progress_callback=None):
    # Read CSV file
    ratings_df = pd.read_csv(ratings_file)

    # Connect to SQLite database (or create it)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    total_movies = len(ratings_df)  # Total movies to process
    processed_movies = 0            # Track processed movies count

    # Iterate through the ratings dataframe and insert/update data into the database
    for index, row in ratings_df.iterrows():
        username = row['Username']
        movie_name = row['Movie Name']
        rating = row['Rating']  # Assuming rating scaling is still needed
        print(f'{movie_name} {rating}')

        # Check if the movie already exists in the movie_details table
        cursor.execute('SELECT 1 FROM movie_details WHERE movie_name = ?', (movie_name,))
        movie_exists = cursor.fetchone()

        if not movie_exists:
            print(f'{movie_name} doesn't exist in db')
            details = get_movie_details(movie_name)

            if details:
                g = adjust_list(details['genres'])
                d = adjust_list(details['director'].split(','))
                l = details['language'].split(',')
                c = details['country'].split(',')

                cursor.execute('''INSERT INTO movie_details (movie_name, year, director1, director2, cast1, cast2, cast3, cast4, cast5,
                                duration, country, genre1, genre2, genre3, genre4, genre5, language)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                (movie_name, details['year'], d[0], d[1], details['cast'][0], details['cast'][1],
                                details['cast'][2], details['cast'][3], details['cast'][4], details['duration'],
                                c[0], g[0], g[1], g[2], g[3], g[4], l[0]))

                conn.commit()

        # Check if a record with the same username and movie_name exists in the users table
        cursor.execute('''SELECT rating FROM users WHERE username = ? AND movie_name = ?''',
                        (username, movie_name))
        user_record = cursor.fetchone()

        if user_record:
            existing_rating = user_record[0]
            if existing_rating != rating:
                cursor.execute('''UPDATE users SET rating = ? WHERE username = ? AND movie_name = ?''',
                                (rating, username, movie_name))
        else:
            cursor.execute('''INSERT INTO users (username, movie_name, rating)
                                VALUES (?, ?, ?)''', (username, movie_name, rating))

        conn.commit()

        # Update progress after processing each movie
        processed_movies += 1
        if progress_callback:
            progress_callback(processed_movies, total_movies)

    conn.close()
