import streamlit as st
import pandas as pd
import sqlite3
from functions import collect_and_save_user_movies, create_and_populate_db

# Title and description
st.title("Letterboxd User Stats")
st.write("Enter your Letterboxd username to view statistics about your movie-watching habits.")

# Get username input
username = st.text_input("Enter your Letterboxd username:", "")

# Run only when username is entered
if username:
    # File paths
    ratings_file = 'user.csv'
    db_name = 'movies.db'

    # Collect movies data and populate the SQLite database
    collect_and_save_user_movies(username)
    create_and_populate_db(ratings_file, username, db_name)

    # Connect to the SQLite database
    conn = sqlite3.connect(db_name)
    
    # Fetch total number of films watched
    total_films = pd.read_sql_query(f"SELECT COUNT(*) FROM users WHERE username = '{username}'", conn).iloc[0, 0]
    
    # Calculate total hours watched
    total_duration_query = """
        SELECT SUM(CAST(duration AS INTEGER)) FROM movie_details 
        WHERE movie_name IN (SELECT movie_name FROM users WHERE username = ?)
    """
    total_hours = pd.read_sql_query(total_duration_query, conn, params=(username,)).iloc[0, 0] or 0
    total_hours = total_hours // 60  # Convert minutes to hours

    # Fetch count of different directors
    unique_directors_query = """
        SELECT COUNT(DISTINCT director1) + COUNT(DISTINCT director2) FROM movie_details 
        WHERE movie_name IN (SELECT movie_name FROM users WHERE username = ?)
    """
    different_directors = pd.read_sql_query(unique_directors_query, conn, params=(username,)).iloc[0, 0]

    # Fetch count of different countries
    unique_countries_query = """
        SELECT COUNT(DISTINCT country) FROM movie_details 
        WHERE movie_name IN (SELECT movie_name FROM users WHERE username = ?)
    """
    different_countries = pd.read_sql_query(unique_countries_query, conn, params=(username,)).iloc[0, 0]

    # Display general stats
    st.write(f"**Total Films:** {total_films}")
    st.write(f"**Total Hours:** {total_hours} hours")
    st.write(f"**Different Directors:** {different_directors}")
    st.write(f"**Different Countries:** {different_countries}")

    # Find most watched genres, languages, and countries
    def get_most_watched(column_name):
        query = f"""
            SELECT {column_name}, COUNT(*) AS count FROM movie_details 
            WHERE movie_name IN (SELECT movie_name FROM users WHERE username = ?)
            GROUP BY {column_name} ORDER BY count DESC LIMIT 5
        """
        result = pd.read_sql_query(query, conn, params=(username,))
        return result

    # Display most watched genres
    most_watched_genres = get_most_watched("genre1")
    st.write("**Most Watched Genres:**")
    st.dataframe(most_watched_genres)

    # Display most watched languages
    most_watched_languages = get_most_watched("language")
    st.write("**Most Watched Languages:**")
    st.dataframe(most_watched_languages)

    # Display most watched countries
    most_watched_countries = get_most_watched("country")
    st.write("**Most Watched Countries:**")
    st.dataframe(most_watched_countries)

    # Close database connection
    conn.close()
