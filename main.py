import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import re
import os
import zipfile
from io import BytesIO
from PIL import Image

# Spotify API credentials (replace with your own)
# from dotenv import load_dotenv
# load_dotenv(".env")
# load_dotenv()
# CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
# CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# print("SPOTIPY_CLIENT_ID:", os.getenv("SPOTIPY_CLIENT_ID"))
# print("SPOTIPY_CLIENT_SECRET:", os.getenv("SPOTIPY_CLIENT_SECRET"))

# Fetch credentials securely from Streamlit secrets
CLIENT_ID = st.secrets["SPOTIPY_CLIENT_ID"]
CLIENT_SECRET = st.secrets["SPOTIPY_CLIENT_SECRET"]

# Check if credentials are loaded properly
if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("Missing Spotify API credentials. Check your .env file.")

# Initialize Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

def sanitize_filename(filename):
    """Removes invalid characters from filenames."""
    return re.sub(r'[<>:"/\\|?*]', '', filename)  # Removes special characters

def fetch_image(url):
    """Fetches the album cover image and returns it as a PIL Image."""
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        return None

def save_image_locally(image, filename, folder):
    """Saves the image to the specified folder."""
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    image.save(filepath, format='JPEG')
    return filepath

def create_zip(images):
    """Creates a zip file containing all images and returns it as BytesIO."""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename, image in images:
            img_bytes = BytesIO()
            image.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            zip_file.writestr(filename, img_bytes.read())
    zip_buffer.seek(0)
    return zip_buffer

def get_playlist_tracks(playlist_url):
    """Fetches tracks from a Spotify playlist and returns album cover images."""
    playlist_id = playlist_url.split("/")[-1].split("?")[0]
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    
    cover_images = []
    
    for track in tracks:
        track_info = track['track']
        song_name = track_info['name']
        artist_name = track_info['artists'][0]['name']
        album_cover_url = track_info['album']['images'][0]['url']

        image = fetch_image(album_cover_url)
        
        if image:
            filename = f"{sanitize_filename(song_name)}_{sanitize_filename(artist_name)}.jpg"
            cover_images.append((filename, image))
    
    return cover_images

# Streamlit UI
st.title("Spotify Cover Image Extractor")
url = st.text_input("Enter public playlist URL")
save_folder = st.text_input("Enter folder name to save images locally (optional)")
if st.button("Extract Images"):
    if url:
        covers = get_playlist_tracks(url)
        if covers:
            st.success("Images fetched successfully!")
            for filename, image in covers:
                #st.image(image, caption=filename, use_container_width=True)
                
                # Convert image to BytesIO for download
                img_bytes = BytesIO()
                image.save(img_bytes, format='JPEG')
                img_bytes.seek(0)
                
                # Download button
                st.download_button(
                    label=f"Download {filename}",
                    data=img_bytes,
                    file_name=filename,
                    mime="image/jpeg"
                )
                
                # Save locally if folder name is provided
                if save_folder:
                    save_path = save_image_locally(image, filename, save_folder)
                    st.write(f"Saved locally: {save_path}")
            
            # Create and provide zip download
            zip_buffer = create_zip(covers)
            st.download_button(
                label="Download All Images as ZIP",
                data=zip_buffer,
                file_name="album_covers.zip",
                mime="application/zip"
            )
        else:
            st.error("Failed to fetch images. Check the playlist URL.")
    else:
        st.warning("Please enter a valid Spotify playlist URL.")
