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

def insert_csv(i):
    # Assuming 'link' contains the URL to scrape
    link = f'https://letterboxd.com/{i}/films/by/date/'

    # Extract the username from the link
    username = d[i]

    # Fetch the page content
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')

    # List to store movie details
    movies = []

    # Find all the movie items
    movie_items = soup.select('ul.poster-list li.poster-container')[:30]  # Limit to the first 30

    for movie in movie_items:
        # Get the movie name from the alt attribute of the image tag
        movie_name = movie.find('img').get('alt')
        
        # Attempt to find the rating span; if not found, assign 'No rating'
        rating_span = movie.select_one('p.poster-viewingdata .rating')
        rating = convert_rating_to_integer(rating_span.text if rating_span else 'No rating')

        if rating == 0:
            rating = None
        
        # Append movie details to the list
        movies.append((username, movie_name, rating))

    # Specify the CSV file name based on the username
    csv_file = f'D:\moviebot\csv files\user.csv'

    # Create a set to store existing entries for uniqueness
    existing_entries = set()

    # Read existing entries from the user's CSV file if it exists
    if os.path.exists(csv_file):
        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            # Skip the header row
            next(reader)
            # Populate the set with existing entries
            for row in reader:
                existing_entries.add((row[0], row[1], row[2]))

    # Open the CSV file in append mode
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write the header if the file is new
        if file.tell() == 0:  # Check if the file is empty
            writer.writerow(['Username', 'Movie Name', 'Rating'])
        
        # Write the movie data only if it does not exist
        for movie in movies:
            if movie not in existing_entries:
                writer.writerow(movie)


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
def create_and_populate_db(ratings_file, username, db_name='movies.db'):
    # Read CSV file
    ratings_df = pd.read_csv(ratings_file)

    # Connect to SQLite database (or create it)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Iterate through the ratings dataframe and insert/update data into the database
    for index, row in ratings_df.iterrows():
        #try:
        username = row['Username']
        movie_name = row['Movie Name']
        rating = row['Rating']  # Assuming rating scaling is still needed

        # Check if the movie already exists in the movie_details table
        cursor.execute('SELECT 1 FROM movie_details WHERE movie_name = ?',
                        (movie_name,))
        movie_exists = cursor.fetchone()

        if not movie_exists:
            # Get movie details from IMDb using the movie name
            details = get_movie_details(movie_name)

            if details:

                # Retrieve and adjust the genres
                g = details['genres'] + [''] * (5 - len(details['genres'])) if details['genres'] else [''] * 5
                g = adjust_list(g)

                d = details['director'].split(',')
                d = adjust_list(d)

                l = details['language'].split(',')
                c = details['country'].split(',')

                # Insert movie details into movie_details table
                cursor.execute('''INSERT INTO movie_details (movie_name, year, director1, director2, cast1, cast2, cast3, cast4, cast5,
                                duration, country, genre1, genre2, genre3, genre4, genre5, language)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                (movie_name, details['year'], d[0], d[1], details['cast'][0], details['cast'][1],
                                details['cast'][2], details['cast'][3], details['cast'][4], details['duration'],
                                c[0], g[0], g[1], g[2], g[3], g[4], l[0]))

                # Print details of the newly inserted movie
                try:
                    print(f"Inserted into movie_details: {movie_name} ({details['year']})")
                except:
                    print('')
                conn.commit()

        # Check if a record with the same username and movie_name exists in the users table
        cursor.execute('''SELECT rating FROM users WHERE username = ? AND movie_name = ?''',
                        (username, movie_name))
        user_record = cursor.fetchone()

        if user_record:
            existing_rating = user_record[0]

            # If the record exists but the rating is different, update the rating
            if existing_rating != rating:
                cursor.execute('''UPDATE users SET rating = ? WHERE username = ? AND movie_name = ?''',
                                (rating, username, movie_name))
                try:
                    print(f"Updated rating for {username}, {movie_name} from {existing_rating} to {rating}")
                except:
                    print('')
        else:
            # If no record exists, insert the new data
            cursor.execute('''INSERT INTO users (username, movie_name, rating)
                                VALUES (?, ?, ?)''', (username, movie_name, rating))
            try:
                print(f"Inserted into users: {username}, {movie_name}, Rating: {rating}")
            except:
                print('..')
            print('-' * 50)
            
        conn.commit()

    conn.close()
