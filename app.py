import streamlit as st
import pandas as pd
import sqlite3
import time
from functions import collect_and_save_user_movies, create_and_populate_db

# Title and description
st.title("Letterboxd User Stats")
st.write("Enter your Letterboxd username to view statistics about your movie-watching habits.")

# Get username input
username = st.text_input("Enter your Letterboxd username:", "")

if username:
    # File paths
    ratings_file = 'user.csv'
    db_name = 'movies.db'

    with st.spinner("Collecting movies data from Letterboxd..."):
        collect_and_save_user_movies(username)
        st.write("✅ Data collection from Letterboxd complete!")

    # Initialize the loading bar for populating database
    st.write("Populating the database with movie details...")
    db_progress = st.progress(0)

    # Progress callback function
    def progress_callback(processed, total):
        db_progress.progress(processed / total)

    # Populate the database with the progress callback
    create_and_populate_db(ratings_file, username, db_name, progress_callback=progress_callback)
    st.write("✅ Database population complete!")

    # Connect to the SQLite database
    conn = sqlite3.connect(db_name)

    # Display user stats as before
    st.write("Calculating your movie-watching stats...")
    stats_progress = st.progress(0)

    total_films = pd.read_sql_query(f"SELECT COUNT(*) FROM users WHERE username = '{username}'", conn).iloc[0, 0]
    stats_progress.progress(20)

    total_duration_query = """
        SELECT SUM(CAST(duration AS INTEGER)) FROM movie_details 
        WHERE movie_name IN (SELECT movie_name FROM users WHERE username = ?)
    """
    total_hours = pd.read_sql_query(total_duration_query, conn, params=(username,)).iloc[0, 0] or 0
    total_hours = total_hours // 60
    stats_progress.progress(40)

    unique_directors_query = """
        SELECT COUNT(DISTINCT director1) + COUNT(DISTINCT director2) FROM movie_details 
        WHERE movie_name IN (SELECT movie_name FROM users WHERE username = ?)
    """
    different_directors = pd.read_sql_query(unique_directors_query, conn, params=(username,)).iloc[0, 0]
    stats_progress.progress(60)

    unique_countries_query = """
        SELECT COUNT(DISTINCT country) FROM movie_details 
        WHERE movie_name IN (SELECT movie_name FROM users WHERE username = ?)
    """
    different_countries = pd.read_sql_query(unique_countries_query, conn, params=(username,)).iloc[0, 0]
    stats_progress.progress(80)

    # Display stats
    st.write(f"**Total Films:** {total_films}")
    st.write(f"**Total Hours:** {total_hours} hours")
    st.write(f"**Different Directors:** {different_directors}")
    st.write(f"**Different Countries:** {different_countries}")
    stats_progress.progress(100)

    # Helper function to get most-watched attributes
    def get_most_watched(column_name):
        query = f"""
            SELECT {column_name}, COUNT(*) AS count FROM movie_details 
            WHERE movie_name IN (SELECT movie_name FROM users WHERE username = ?)
            GROUP BY {column_name} ORDER BY count DESC LIMIT 5
        """
        return pd.read_sql_query(query, conn, params=(username,))

    # Display additional stats
    st.write("**Most Watched Genres:**")
    st.dataframe(get_most_watched("genre1"))

    st.write("**Most Watched Languages:**")
    st.dataframe(get_most_watched("language"))

    st.write("**Most Watched Countries:**")
    st.dataframe(get_most_watched("country"))

    # Close database connection
    conn.close()
