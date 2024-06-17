Sure! Here is the updated README file for your Streamlit app:

# Letterboxd Stats 🌎

## Features

- Scrapes movie details from Letterboxd based on your username
- Provides statistics such as total hours watched, distinct directors, countries, and languages
- Displays movie count by year in a line graph
- Shows top languages, countries, and genres in bar charts
- Lists top directors with the number of movies watched
- Dynamic data collection with progress updates

## Usage

1. Visit the app at [Letterboxd Stats](https://letterboxdstats.streamlit.app/)
2. Enter your Letterboxd username in the text input field.
3. The app will scrape your profile and display basic details.
4. View various statistics and insights about your movie-watching habits.

## Functions

### `scrape_profile(username)`

Scrapes the Letterboxd profile of the given username and returns the name, bio, and profile image URL.

### `extract_movies(url)`

Extracts movie slugs from a given Letterboxd URL.

### `extract_all_movies(username)`

Extracts all movie slugs for the given username.

### `fetch_movie_details(username, movie_titles, stop_flag, data_collection_text)`

Fetches movie details from IMDb and stores them in an SQLite database.

### `get_movie_statistics(username)`

Returns statistics such as total hours watched, distinct directors, countries, and languages for the given username.

### `get_year_movie_count(username)`

Returns the count of movies watched per year for the given username.

### `get_top_languages(username)`

Returns the top languages of movies watched by the given username.

### `get_top_countries(username)`

Returns the top countries of movies watched by the given username.

### `count_genre_entries(username)`

Counts the number of movies in each genre for the given username.

### `get_top_directors(username)`

Returns the top directors based on the number of movies watched by the given username.

### `create_bar_chart(data, x_label, y_label)`

Creates a bar chart using Plotly for the given data.

### `mask_to_circle(img)`

Masks an image to a circular shape.

## Dependencies

- `requests`
- `beautifulsoup4`
- `streamlit`
- `Pillow`
- `plotly`
- `altair`
- `sqlite3`
- `imdbpy`
- `matplotlib`
- `numpy`
- `pandas`

Enjoy exploring your Letterboxd stats! 📽️🎬🍿
