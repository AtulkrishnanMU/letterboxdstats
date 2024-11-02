import streamlit as st
import pandas as pd
import sqlite3
import time
from functions import collect_and_save_user_movies, create_and_populate_db

import os
import requests

# Access the token from environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "AtulkrishnanMU/letterboxdstats"
FILE_PATH = "movies.db"

# Title and description
st.markdown("# :rainbow[Letterboxd User Stats]")
#st.title("[Letterboxd User Stats]")
# Add GitHub profile promotion
st.markdown(
    "👤 Created by: [AtulkrishnanMU](https://github.com/AtulkrishnanMU)")

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

    # Initialize the loading bar and percentage display for database population
    st.write("Populating the database with movie details...")
    db_progress = st.progress(0)
    db_progress_text = st.empty()  # Placeholder for the percentage text

    # Progress callback function with percentage display
    def progress_callback(processed, total):
        percentage = int((processed / total) * 100)
        db_progress.progress(processed / total)
        db_progress_text.write(f"{percentage}% complete")  # Update percentage text

    # Populate the database with the progress callback
    create_and_populate_db(ratings_file, username, db_name, progress_callback=progress_callback)
    st.write("✅ Database population complete!")

    # Connect to the SQLite database
    conn = sqlite3.connect(db_name)

    # Use a spinner for calculating stats
    with st.spinner("Calculating your movie-watching stats..."):
        # Calculation steps
        total_films = pd.read_sql_query(f"SELECT COUNT(*) FROM users WHERE username = '{username}'", conn).iloc[0, 0]

        total_duration_query = """
            SELECT SUM(CAST(duration AS INTEGER)) FROM movie_details 
            WHERE movie_name IN (SELECT movie_name FROM users WHERE username = ?)
        """
        total_hours = pd.read_sql_query(total_duration_query, conn, params=(username,)).iloc[0, 0] or 0
        total_hours = total_hours // 60

        unique_directors_query = """
            SELECT COUNT(DISTINCT director1) + COUNT(DISTINCT director2) FROM movie_details 
            WHERE movie_name IN (SELECT movie_name FROM users WHERE username = ?)
        """
        different_directors = pd.read_sql_query(unique_directors_query, conn, params=(username,)).iloc[0, 0]

        unique_countries_query = """
            SELECT COUNT(DISTINCT country) FROM movie_details 
            WHERE movie_name IN (SELECT movie_name FROM users WHERE username = ?)
        """
        different_countries = pd.read_sql_query(unique_countries_query, conn, params=(username,)).iloc[0, 0]

    # Display stats after spinner completes
    st.write(f"**Total Films:** {total_films}")
    st.write(f"**Total Hours:** {total_hours} hours")
    st.write(f"**Different Directors:** {different_directors}")
    st.write(f"**Different Countries:** {different_countries}")

    # Helper function to get most-watched attributes
    def get_most_watched(column_name):
        query = f"""
            SELECT {column_name} AS category, COUNT(*) AS count FROM movie_details 
            WHERE movie_name IN (SELECT movie_name FROM users WHERE username = ?)
            GROUP BY {column_name} ORDER BY count DESC LIMIT 5
        """
        return pd.read_sql_query(query, conn, params=(username,))

    # Display additional stats as bar charts
    st.write("**Most Watched Genres:**")
    most_watched_genres = get_most_watched("genre1")
    st.bar_chart(most_watched_genres.set_index("category"))

    st.write("**Most Watched Languages:**")
    most_watched_languages = get_most_watched("language")
    st.bar_chart(most_watched_languages.set_index("category"))

    st.write("**Most Watched Countries:**")
    most_watched_countries = get_most_watched("country")
    st.bar_chart(most_watched_countries.set_index("category"))

    # Save changes to GitHub
    def upload_to_github(file_path, repo, token, commit_message="Update movies database"):
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        
        # Read the file and encode in base64 for GitHub API
        with open(db_name, "rb") as file:
            content = base64.b64encode(file.read()).decode("utf-8")

        # Check if the file already exists to get the SHA
        response = requests.get(url, headers={"Authorization": f"token {token}"})
        if response.status_code == 200:
            sha = response.json().get("sha")
        else:
            sha = None  # File does not exist yet

        # Prepare payload
        data = {
            "message": commit_message,
            "content": content,
            "branch": "main",
        }
        if sha:
            data["sha"] = sha

        # Upload to GitHub
        response = requests.put(url, json=data, headers={"Authorization": f"token {token}"})
        if response.status_code == 201 or response.status_code == 200:
            st.write("Database successfully updated on GitHub.")
        else:
            st.write("Failed to update database on GitHub.")
            st.write(response.json())

    # Call the function to upload to GitHub
    upload_to_github(FILE_PATH, REPO_NAME, GITHUB_TOKEN)
    
    # Close database connection
    conn.close()
