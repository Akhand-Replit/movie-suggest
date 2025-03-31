import streamlit as st
import requests
import json
import random
import google.generativeai as genai
from PIL import Image
import io
import base64
import time

# App configuration
st.set_page_config(
    page_title="SVOMO RECOMMENDATION",
    page_icon="🎬",
    layout="wide",
)

# Load secrets
def get_secrets():
    try:
        # For local development with secrets.toml
        tmdb_api_key = st.secrets["tmdb_api_key"]
        gemini_api_key = st.secrets["gemini_api_key"]
    except:
        # Fallback for development (replace with your actual keys for testing)
        st.error("⚠️ API keys not found in secrets. Please configure secrets.toml file.")
        tmdb_api_key = "your_tmdb_api_key"
        gemini_api_key = "your_gemini_api_key"
    
    return tmdb_api_key, gemini_api_key

tmdb_api_key, gemini_api_key = get_secrets()

# Initialize Gemini API
genai.configure(api_key=gemini_api_key)
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}
model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config
)

# Custom CSS for retro-futuristic UI
def load_css():
    st.markdown("""
    <style>
    /* Retro-futuristic theme */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&display=swap');
    
    .main {
        background-color: #0a0a1a;
        color: #d1e0ff;
    }
    
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        color: #00ffcc;
        text-shadow: 0 0 10px #00ffcc80;
    }
    
    .stButton>button {
        background-color: #ff00aa;
        color: white;
        border: 2px solid #ff00aa;
        border-radius: 5px;
        font-family: 'Orbitron', sans-serif;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #0a0a1a;
        border-color: #ff00aa;
        color: #ff00aa;
        box-shadow: 0 0 15px #ff00aa80;
    }
    
    .recommendation-card {
        background: linear-gradient(145deg, #15153a, #0a0a1a);
        border: 1px solid #3a3a8c;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.7), 0 0 20px rgba(0, 255, 204, 0.2);
        transition: all 0.3s ease;
    }
    
    .recommendation-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.8), 0 0 30px rgba(0, 255, 204, 0.3);
    }
    
    .progress-bar {
        height: 10px;
        background: linear-gradient(90deg, #ff00aa, #00ffcc);
        border-radius: 5px;
        margin-bottom: 20px;
    }
    
    .neon-text {
        color: #00ffcc;
        text-shadow: 0 0 10px #00ffcc80;
    }
    
    .glow-container {
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 0 15px #00ffcc40;
    }
    
    /* Custom radio buttons */
    div.st-emotion-cache-16txtl3 div {
        background-color: #15153a;
        color: #d1e0ff;
        border: 1px solid #3a3a8c;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        transition: all 0.3s;
    }
    
    div.st-emotion-cache-16txtl3 div:hover {
        background-color: #1f1f4f;
        box-shadow: 0 0 10px rgba(0, 255, 204, 0.3);
    }
    
    .footer {
        margin-top: 50px;
        padding: 20px;
        text-align: center;
        border-top: 1px solid #3a3a8c;
    }
    
    </style>
    """, unsafe_allow_html=True)

load_css()

# Functions for TMDB API
def get_tmdb_config():
    url = "https://api.themoviedb.org/3/configuration"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {tmdb_api_key}"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to get TMDB configuration: {response.text}")
        return None

def search_movies(query, media_type="movie"):
    url = f"https://api.themoviedb.org/3/search/{media_type}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {tmdb_api_key}"
    }
    params = {
        "query": query,
        "include_adult": "false",
        "language": "en-US",
        "page": 1
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to search movies: {response.text}")
        return None

def get_movie_details(movie_id, media_type="movie"):
    url = f"https://api.themoviedb.org/3/{media_type}/{movie_id}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {tmdb_api_key}"
    }
    params = {
        "language": "en-US",
        "append_to_response": "credits,videos"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to get movie details: {response.text}")
        return None

def get_image_url(poster_path, base_url, poster_size):
    if poster_path:
        return f"{base_url}{poster_size}{poster_path}"
    return "https://via.placeholder.com/300x450?text=No+Image+Available"

# Main application logic
def main():
    # Header with glowing effect
    st.markdown("<h1 class='neon-text' style='text-align: center;'>SVOMO RECOMMENDATION</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-bottom: 30px;'>Your AI-powered movie and anime recommendation system</p>", unsafe_allow_html=True)
    
    # Initialize session state
    if 'stage' not in st.session_state:
        st.session_state.stage = 'persona'
    
    if 'persona' not in st.session_state:
        st.session_state.persona = {}
    
    if 'mood_context' not in st.session_state:
        st.session_state.mood_context = {}
    
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = []
    
    # Get TMDB configuration
    if 'tmdb_config' not in st.session_state:
        st.session_state.tmdb_config = get_tmdb_config()
    
    # STAGE 1: User Persona Collection
    if st.session_state.stage == 'persona':
        with st.container():
            st.markdown("<div class='glow-container'><h2>Tell us about yourself</h2></div>", unsafe_allow_html=True)
            
            # Use Gemini to generate persona questions if they don't exist yet
            if 'persona_questions' not in st.session_state:
                with st.spinner("Crafting personalized questions..."):
                    prompt = """
                    Generate 4 questions to understand a user's movie/anime watching preferences.
                    First question must ask if they prefer anime or movies.
                    Return the result as a JSON with this structure:
                    {
                        "questions": [
                            {
                                "id": "q1",
                                "text": "Question text here",
                                "options": ["Option 1", "Option 2", "Option 3"]
                            },
                            {
                                "id": "q2",
                                ...
                            }
                        ]
                    }
                    """
                    response = model.generate_content(prompt)
                    try:
                        questions_json = json.loads(response.text)
                        st.session_state.persona_questions = questions_json["questions"]
                    except:
                        # Fallback questions if API fails
                        st.session_state.persona_questions = [
                            {
                                "id": "content_type",
                                "text": "Do you prefer watching anime or movies?",
                                "options": ["Anime", "Movies", "Both equally"]
                            },
                            {
                                "id": "preferred_genres",
                                "text": "Which genres do you usually enjoy watching?",
                                "options": ["Action/Adventure", "Drama/Romance", "Comedy", "Sci-Fi/Fantasy"]
                            },
                            {
                                "id": "language_preference",
                                "text": "Which language content do you prefer?",
                                "options": ["English", "Japanese", "Korean", "Bollywood/Hindi", "Multiple languages"]
                            },
                            {
                                "id": "viewing_frequency",
                                "text": "How often do you watch movies or shows?",
                                "options": ["Daily", "Few times a week", "Weekends only", "Occasionally"]
                            }
                        ]
            
            # Display persona questions
            for q in st.session_state.persona_questions:
                st.session_state.persona[q["id"]] = st.radio(
                    q["text"],
                    options=q["options"],
                    key=f"persona_{q['id']}"
                )
            
            if st.button("Next: Tell us about your mood", key="persona_next"):
                st.session_state.stage = 'mood'
                st.experimental_rerun()
    
    # STAGE 2: Mood and Context Collection
    elif st.session_state.stage == 'mood':
        with st.container():
            st.markdown("<div class='glow-container'><h2>What are you in the mood for?</h2></div>", unsafe_allow_html=True)
            
            # Generate mood questions based on persona if they don't exist yet
            if 'mood_questions' not in st.session_state:
                with st.spinner("Analyzing your preferences..."):
                    persona_json = json.dumps(st.session_state.persona)
                    prompt = f"""
                    Based on this user persona: {persona_json}
                    
                    Generate 5-7 questions to understand what kind of movie/show the user wants to watch right now.
                    Include questions about:
                    - Who they're watching with
                    - Their current mood
                    - Time available for watching
                    - Themes they're interested in
                    - Any other relevant factors

                    Return the result as a JSON with this structure:
                    {{
                        "questions": [
                            {{
                                "id": "q1",
                                "text": "Question text here",
                                "options": ["Option 1", "Option 2", "Option 3"]
                            }},
                            {{
                                "id": "q2",
                                ...
                            }}
                        ]
                    }}
                    """
                    response = model.generate_content(prompt)
                    try:
                        questions_json = json.loads(response.text)
                        st.session_state.mood_questions = questions_json["questions"]
                    except:
                        # Fallback mood questions if API fails
                        st.session_state.mood_questions = [
                            {
                                "id": "social_context",
                                "text": "Who are you watching with?",
                                "options": ["Alone", "With friend(s)", "With family", "With partner"]
                            },
                            {
                                "id": "current_mood",
                                "text": "What's your current mood?",
                                "options": ["Happy/Excited", "Relaxed/Chill", "Sad/Emotional", "Thoughtful/Introspective"]
                            },
                            {
                                "id": "available_time",
                                "text": "How much time do you have available?",
                                "options": ["Under 2 hours", "2-3 hours", "Multiple sessions", "Binge-watch a series"]
                            },
                            {
                                "id": "content_theme",
                                "text": "What theme are you interested in right now?",
                                "options": ["Love/Romance", "Action/Excitement", "Mystery/Suspense", "Escapism/Fantasy"]
                            },
                            {
                                "id": "content_recency",
                                "text": "Do you prefer new releases or classics?",
                                "options": ["New releases (last 2 years)", "Recent (last 5 years)", "Timeless classics", "Don't care"]
                            }
                        ]
            
            # Display mood questions
            for q in st.session_state.mood_questions:
                st.session_state.mood_context[q["id"]] = st.radio(
                    q["text"],
                    options=q["options"],
                    key=f"mood_{q['id']}"
                )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Back to Persona", key="mood_back"):
                    st.session_state.stage = 'persona'
                    st.experimental_rerun()
            
            with col2:
                if st.button("Get Recommendations", key="mood_next"):
                    st.session_state.stage = 'searching'
                    st.experimental_rerun()
    
    # STAGE 3: Searching for Recommendations
    elif st.session_state.stage == 'searching':
        st.markdown("<div class='glow-container'><h2>Finding your perfect match...</h2></div>", unsafe_allow_html=True)
        
        progress_text = "Our AI is searching the multiverse of entertainment for you..."
        my_bar = st.progress(0, text=progress_text)
        
        # Simulated search progress
        for percent_complete in range(0, 101, 20):
            time.sleep(0.5)  # Simulate processing time
            my_bar.progress(percent_complete, text=f"{progress_text} {percent_complete}%")
        
        # Generate recommendations based on user inputs
        persona_json = json.dumps(st.session_state.persona)
        mood_json = json.dumps(st.session_state.mood_context)
        
        with st.spinner("AI is crafting your personalized recommendations..."):
            prompt = f"""
            Based on this user persona: {persona_json}
            And their current mood/context: {mood_json}
            
            Recommend exactly 3 movies or shows (based on their preference for anime vs movies).
            
            For each recommendation, provide:
            1. Title (exact spelling is important)
            2. Year of release (if known)
            3. Type (movie, TV show, or anime)
            4. A brief overview of why this would appeal to the user

            Return the response in this JSON format:
            {{
                "recommendations": [
                    {{
                        "title": "Title here",
                        "year": "Year here or null",
                        "type": "movie/show/anime",
                        "explanation": "Why this recommendation matches their preferences"
                    }},
                    ...
                ]
            }}
            """
            
            try:
                response = model.generate_content(prompt)
                recommendations_data = json.loads(response.text)
                
                # Process each recommendation and get details from TMDB
                processed_recommendations = []
                
                for rec in recommendations_data["recommendations"]:
                    # Determine media type for API
                    media_type = "movie"
                    if rec["type"].lower() in ["show", "tv show", "tv", "series"]:
                        media_type = "tv"
                    elif rec["type"].lower() == "anime":
                        media_type = "tv"  # Most anime are categorized as TV shows in TMDB
                    
                    # Search for the title
                    search_results = search_movies(rec["title"], media_type)
                    
                    if search_results and search_results["results"]:
                        # Get the first result
                        result = search_results["results"][0]
                        movie_id = result["id"]
                        
                        # Get detailed information
                        details = get_movie_details(movie_id, media_type)
                        
                        if details:
                            # Get image URL
                            base_url = st.session_state.tmdb_config["images"]["secure_base_url"]
                            poster_size = st.session_state.tmdb_config["images"]["poster_sizes"][3]  # Medium size
                            image_url = get_image_url(details.get("poster_path"), base_url, poster_size)
                            
                            # Create recommendation object
                            recommendation = {
                                "id": movie_id,
                                "title": details.get("title", details.get("name", rec["title"])),
                                "year": details.get("release_date", details.get("first_air_date", "")),
                                "overview": details.get("overview", ""),
                                "image_url": image_url,
                                "explanation": rec["explanation"],
                                "media_type": media_type,
                                "genres": [genre["name"] for genre in details.get("genres", [])]
                            }
                            
                            processed_recommendations.append(recommendation)
                
                st.session_state.recommendations = processed_recommendations
                st.session_state.stage = 'results'
                st.experimental_rerun()
                
            except Exception as e:
                st.error(f"Error generating recommendations: {str(e)}")
                # Fallback in case of API error
                st.session_state.stage = 'results'
                st.session_state.recommendations = []  # Empty recommendations
                st.experimental_rerun()
    
    # STAGE 4: Display Recommendations
    elif st.session_state.stage == 'results':
        st.markdown("<div class='glow-container'><h2>Your Personalized Recommendations</h2></div>", unsafe_allow_html=True)
        
        if not st.session_state.recommendations:
            st.warning("We couldn't find recommendations that match your preferences. Please try again.")
            if st.button("Start Over", key="empty_restart"):
                # Reset session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.experimental_rerun()
        else:
            # Display recommendations in cards
            cols = st.columns(len(st.session_state.recommendations))
            
            for i, rec in enumerate(st.session_state.recommendations):
                with cols[i]:
                    st.markdown(f"""
                    <div class='recommendation-card'>
                        <h3>{rec['title']}</h3>
                        <p><strong>Year:</strong> {rec['year'][:4] if rec['year'] else 'N/A'}</p>
                        <img src="{rec['image_url']}" alt="{rec['title']}" style="width:100%; border-radius:5px; margin:10px 0;">
                        <p><strong>Genres:</strong> {', '.join(rec['genres'])}</p>
                        <p><strong>Overview:</strong> {rec['overview'][:150]}...</p>
                        <div style="margin-top:15px; padding:10px; background:#15153a; border-radius:5px;">
                            <p><strong>Why we recommend this:</strong> {rec['explanation']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Restart button
            if st.button("Start Over", key="restart"):
                # Reset session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.experimental_rerun()
                
    # Footer
    st.markdown("""
    <div class="footer">
        <p>SVOMO RECOMMENDATION - Powered by:</p>
        <div style="display: flex; justify-content: center; align-items: center; gap: 30px; margin-top: 15px;">
            <div>
                <img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_square_2-d537fb228cf3ded904ef09b136fe3fec72548ebc1fea3fbbd1ad9e36364db38b.svg" 
                     alt="TMDB" width="80">
            </div>
            <div>
                <img src="https://lh3.googleusercontent.com/vWdgYhn0Nzl75Yq_MbJoUzRcm2Kf9rTRCgHJuhQMZQYPqGmlik2iGrTVP3mBYPn0z9fjGpwv4wnNGGffIJ2K0v2dRrJ_MIh0PlfR-r4" 
                     alt="Google Gemini" width="120">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
