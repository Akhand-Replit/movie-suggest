import streamlit as st
import requests
import json
import random
import time
from PIL import Image
import io
import base64

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
        
        # Validate API keys
        if tmdb_api_key == "YOUR_TMDB_API_KEY_HERE" or gemini_api_key == "YOUR_GEMINI_API_KEY_HERE":
            st.error("⚠️ Please replace the placeholder API keys in your secrets.toml file with actual API keys.")
            tmdb_api_key = None
            gemini_api_key = None
    except Exception as e:
        # Fallback for development (replace with your actual keys for testing)
        st.error(f"⚠️ API keys not found in secrets: {str(e)}. Please configure secrets.toml file.")
        tmdb_api_key = None
        gemini_api_key = None
    
    return tmdb_api_key, gemini_api_key

tmdb_api_key, gemini_api_key = get_secrets()

# Use direct API requests for Gemini instead of the SDK
def call_gemini_api(prompt):
    """Call Gemini API directly using requests instead of the SDK"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.9,
                "topP": 1,
                "topK": 32,
                "maxOutputTokens": 4096
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        # Check for API errors
        if response.status_code != 200:
            st.error(f"Gemini API error: {response.status_code} - {response.text}")
            return None
            
        response_data = response.json()
        
        # Extract the text from the response
        if 'candidates' in response_data and len(response_data['candidates']) > 0:
            candidate = response_data['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                for part in candidate['content']['parts']:
                    if 'text' in part:
                        return part['text']
        
        st.error("Unexpected response format from Gemini API")
        return None
    except Exception as e:
        st.error(f"Failed to call Gemini API: {str(e)}")
        return None

# Test the Gemini API on initialization
def initialize_gemini():
    if not gemini_api_key or gemini_api_key == "YOUR_GEMINI_API_KEY_HERE":
        st.error("Gemini API key not properly configured")
        return False
        
    test_response = call_gemini_api("Hello")
    if test_response:
        return True
    return False

gemini_available = initialize_gemini()

# Custom CSS for dark UI with neon purple outlines
def load_css():
    st.markdown("""
    <style>
    /* Dark UI with neon purple outlines */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&family=Audiowide&family=Syne+Mono&display=swap');
    
    .main {
        background-color: #000000;
        color: #ffffff;
        font-family: 'Orbitron', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Audiowide', cursive;
        color: #ffffff;
        text-align: center;
    }
    
    /* Option buttons styled like in the image */
    div.stRadio > div {
        background-color: transparent !important;
        border: none !important;
    }
    
    div.stRadio > div > label {
        position: relative;
        display: block;
        background-color: transparent;
        border: 2px solid #8a2be2;
        border-radius: 30px;
        color: white;
        padding: 15px 20px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s;
        text-align: left;
        overflow: hidden;
        font-family: 'Orbitron', sans-serif;
        box-shadow: 0 0 5px #8a2be2;
    }
    
    div.stRadio > div > label:hover {
        box-shadow: 0 0 15px #8a2be2;
    }
    
    div.stRadio > div > label[data-baseweb="radio"] input:checked + span {
        background-color: #8a2be2;
    }
    
    /* Question text styling */
    .question-text {
        color: white;
        font-size: 20px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Button styling */
    .stButton > button {
        border: 2px solid #8a2be2;
        border-radius: 30px;
        background-color: transparent;
        color: white;
        font-family: 'Orbitron', sans-serif;
        padding: 10px 20px;
        transition: all 0.3s;
        box-shadow: 0 0 5px #8a2be2;
        width: 100%;
    }
    
    .stButton > button:hover {
        box-shadow: 0 0 15px #8a2be2;
        background-color: rgba(138, 43, 226, 0.2);
    }
    
    /* Card styling */
    .recommendation-card {
        background-color: rgba(0, 0, 0, 0.7);
        border: 2px solid #8a2be2;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 0 10px #8a2be2;
        transition: all 0.3s;
    }
    
    .recommendation-card:hover {
        box-shadow: 0 0 20px #8a2be2;
    }
    
    /* Loading animation */
    @keyframes glow {
        0% {
            box-shadow: 0 0 5px #8a2be2;
        }
        50% {
            box-shadow: 0 0 20px #8a2be2, 0 0 30px #8a2be2;
        }
        100% {
            box-shadow: 0 0 5px #8a2be2;
        }
    }
    
    .loading-container {
        width: 100px;
        height: 100px;
        margin: 50px auto;
        position: relative;
        animation: glow 2s infinite;
    }
    
    .loading-circle {
        width: 100px;
        height: 100px;
        border: 3px solid #8a2be2;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-size: 40px;
    }
    
    /* Progress indicator */
    .progress-dots {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    
    .dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #333;
        border: 1px solid #8a2be2;
        margin: 0 5px;
    }
    
    .dot.active {
        background-color: #8a2be2;
        box-shadow: 0 0 10px #8a2be2;
    }
    
    /* Footer styling */
    .footer {
        margin-top: 50px;
        padding: 20px;
        text-align: center;
        border-top: 1px solid #8a2be2;
    }
    </style>
    """, unsafe_allow_html=True)

load_css()

# Get TMDB configuration
def get_tmdb_config():
    if not tmdb_api_key or tmdb_api_key == "YOUR_TMDB_API_KEY_HERE":
        st.error("TMDB API key not properly configured")
        return None
        
    url = "https://api.themoviedb.org/3/configuration"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {tmdb_api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to get TMDB configuration: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to TMDB API: {str(e)}")
        return None

# Modified search_movies function with better anime handling
def search_movies(query, media_type="movie"):
    if not tmdb_api_key:
        return None
    
    # Clean the query - remove special characters that might affect search
    cleaned_query = query.replace('!', '').replace(':', ' ').strip()
    
    # Special handling for anime titles
    if media_type == "tv" and ("anime" in st.session_state.persona.get("content_type", "").lower() or 
                              any(word in cleaned_query.lower() for word in ["k-on", "nichijou", "aggretsuko"])):
        # Add "anime" to search query for better results
        cleaned_query = f"{cleaned_query} anime"
    
    st.write(f"Searching for: {cleaned_query} as {media_type}")  # Debug
    
    url = f"https://api.themoviedb.org/3/search/{media_type}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {tmdb_api_key}"
    }
    params = {
        "query": cleaned_query,
        "include_adult": "false",
        "language": "en-US",
        "page": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            result = response.json()
            # Debug output
            st.write(f"Found {len(result.get('results', []))} results")
            if not result.get('results'):
                # Try alternative search approach for anime
                if media_type == "tv":
                    # Try searching as movie as fallback
                    st.write(f"Retrying as movie search")
                    return search_movies(query, "movie")
            return result
        else:
            st.error(f"Failed to search movies: {response.status_code}")
            st.write(f"Response: {response.text}")  # Debug
            return None
    except Exception as e:
        st.error(f"Error searching movies: {str(e)}")
        return None

def get_movie_details(movie_id, media_type="movie"):
    if not tmdb_api_key:
        return None
        
    url = f"https://api.themoviedb.org/3/{media_type}/{movie_id}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {tmdb_api_key}"
    }
    params = {
        "language": "en-US",
        "append_to_response": "credits,videos"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to get movie details: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error getting movie details: {str(e)}")
        return None

# Function to get image URL with fallback
def get_image_url(poster_path, base_url, poster_size):
    if poster_path:
        return f"{base_url}{poster_size}{poster_path}"
    return "https://i.ibb.co/s9ZYS5wk/45e6544ed099.jpg"  # Use provided fallback image

# Main application logic
def main():
    # Header
    st.markdown("<h1>SVOMO RECOMMENDATION</h1>", unsafe_allow_html=True)
    
    # Initialize session state
    if 'stage' not in st.session_state:
        st.session_state.stage = 'persona'
        st.session_state.question_index = 0
    
    if 'persona' not in st.session_state:
        st.session_state.persona = {}
    
    if 'mood_context' not in st.session_state:
        st.session_state.mood_context = {}
    
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = []
    
    # Get TMDB configuration
    if 'tmdb_config' not in st.session_state:
        tmdb_config = get_tmdb_config()
        if tmdb_config:
            st.session_state.tmdb_config = tmdb_config
        else:
            # Fallback configuration if API call fails
            st.session_state.tmdb_config = {
                "images": {
                    "secure_base_url": "https://image.tmdb.org/t/p/",
                    "poster_sizes": ["w92", "w154", "w185", "w342", "w500", "w780", "original"]
                }
            }
    
    # STAGE 1: User Persona Collection - One question at a time
    if st.session_state.stage == 'persona':        
        # Define persona questions if they don't exist yet
        if 'persona_questions' not in st.session_state:
            # Fallback questions defined first to ensure they're always available
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
            
            # Try to get personalized questions from Gemini
            with st.spinner("Loading..."):
                st.markdown("""
                <div class="loading-container">
                    <div class="loading-circle">?</div>
                </div>
                """, unsafe_allow_html=True)
                
                if gemini_available:
                    prompt = """
                    Generate 4 questions to understand a user's movie/anime watching preferences.
                    First question must ask if they prefer anime or movies.
                    Return the result as a JSON with this structure ONLY:
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
                    The response must be valid JSON and nothing else.
                    """
                    try:
                        response_text = call_gemini_api(prompt)
                        if response_text:
                            # Find JSON in the response
                            json_start = response_text.find('{')
                            json_end = response_text.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                json_str = response_text[json_start:json_end]
                                questions_json = json.loads(json_str)
                                st.session_state.persona_questions = questions_json["questions"]
                    except Exception as e:
                        pass
        
        # Display one persona question at a time
        if st.session_state.question_index < len(st.session_state.persona_questions):
            q = st.session_state.persona_questions[st.session_state.question_index]
            
            # Progress dots
            st.markdown('<div class="progress-dots">', unsafe_allow_html=True)
            for i in range(len(st.session_state.persona_questions)):
                if i == st.session_state.question_index:
                    st.markdown(f'<div class="dot active"></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="dot"></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display the question
            st.markdown(f'<div class="question-text">{q["text"]}</div>', unsafe_allow_html=True)
            
            # Display options
            selected_option = st.radio(
                "",  # Empty label since we're showing the question text above
                options=q["options"],
                key=f"persona_{q['id']}"
            )
            
            # Store the answer
            st.session_state.persona[q["id"]] = selected_option
            
            # Next button
            if st.button("Next", key=f"next_{st.session_state.question_index}"):
                st.session_state.question_index += 1
                st.rerun()
        else:
            # Move to mood questions
            st.session_state.stage = 'mood'
            st.session_state.question_index = 0
            st.rerun()
    
    # STAGE 2: Mood and Context Collection - One question at a time
    elif st.session_state.stage == 'mood':
        # Generate mood questions if they don't exist yet
        if 'mood_questions' not in st.session_state:
            # Fallback mood questions defined first
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
                }
            ]
            
            # Try to get personalized questions based on persona
            with st.spinner("Loading..."):
                st.markdown("""
                <div class="loading-container">
                    <div class="loading-circle">?</div>
                </div>
                """, unsafe_allow_html=True)
                
                persona_json = json.dumps(st.session_state.persona)
                if gemini_available:
                    # Customize the prompt based on previous answers
                    content_type = st.session_state.persona.get("content_type", "")
                    preferred_genres = st.session_state.persona.get("preferred_genres", "")
                    
                    prompt = f"""
                    Based on this user persona: {persona_json}
                    
                    The user prefers {content_type} and enjoys {preferred_genres}.
                    
                    Generate 4 tailored questions to understand what kind of {content_type.lower()} the user wants to watch right now.
                    Include questions about:
                    - Who they're watching with
                    - Their current mood
                    - Time available for watching
                    - Themes they're interested in

                    Return the result as a JSON with this structure ONLY:
                    {{
                        "questions": [
                            {{
                                "id": "q1",
                                "text": "Question text here",
                                "options": ["Option 1", "Option 2", "Option 3", "Option 4"]
                            }},
                            {{
                                "id": "q2",
                                ...
                            }}
                        ]
                    }}
                    The response must be valid JSON and nothing else.
                    """
                    try:
                        response_text = call_gemini_api(prompt)
                        if response_text:
                            # Find JSON in the response
                            json_start = response_text.find('{')
                            json_end = response_text.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                json_str = response_text[json_start:json_end]
                                questions_json = json.loads(json_str)
                                st.session_state.mood_questions = questions_json["questions"]
                    except Exception as e:
                        pass
        
        # Display one mood question at a time
        if st.session_state.question_index < len(st.session_state.mood_questions):
            q = st.session_state.mood_questions[st.session_state.question_index]
            
            # Progress dots
            st.markdown('<div class="progress-dots">', unsafe_allow_html=True)
            for i in range(len(st.session_state.mood_questions)):
                if i == st.session_state.question_index:
                    st.markdown(f'<div class="dot active"></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="dot"></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display the question
            st.markdown(f'<div class="question-text">{q["text"]}</div>', unsafe_allow_html=True)
            
            # Display options
            selected_option = st.radio(
                "",  # Empty label since we're showing the question text above
                options=q["options"],
                key=f"mood_{q['id']}"
            )
            
            # Store the answer
            st.session_state.mood_context[q["id"]] = selected_option
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("Back", key=f"prev_{st.session_state.question_index}"):
                    if st.session_state.question_index > 0:
                        st.session_state.question_index -= 1
                    else:
                        # Go back to persona questions
                        st.session_state.stage = 'persona'
                        st.session_state.question_index = len(st.session_state.persona_questions) - 1
                    st.rerun()
            
            with col2:
                if st.session_state.question_index < len(st.session_state.mood_questions) - 1:
                    next_text = "Next"
                else:
                    next_text = "Get Recommendations"
                
                if st.button(next_text, key=f"next_{st.session_state.question_index}"):
                    if st.session_state.question_index < len(st.session_state.mood_questions) - 1:
                        st.session_state.question_index += 1
                        st.rerun()
                    else:
                        st.session_state.stage = 'searching'
                        st.rerun()
        else:
            # Move to searching
            st.session_state.stage = 'searching'
            st.rerun()
    
    # STAGE 3: Searching for Recommendations
    elif st.session_state.stage == 'searching':
        # Show loading animation
        st.markdown("""
        <div class="loading-container">
            <div class="loading-circle">?</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate recommendations based on user inputs
        persona_json = json.dumps(st.session_state.persona)
        mood_json = json.dumps(st.session_state.mood_context)
        
        # Default recommendations in case of API failure
        recommendations_data = {
            "recommendations": [
                {
                    "title": "The Matrix",
                    "year": "1999",
                    "type": "movie",
                    "explanation": "A classic sci-fi film with groundbreaking visual effects and a thought-provoking story."
                },
                {
                    "title": "Stranger Things",
                    "year": "2016",
                    "type": "show",
                    "explanation": "A nostalgic sci-fi series with great characters and supernatural mysteries."
                },
                {
                    "title": "Spirited Away",
                    "year": "2001",
                    "type": "anime",
                    "explanation": "A beautifully animated fantasy film with rich storytelling and captivating visuals."
                }
            ]
        }
        
        # Special case for anime fans based on persona
        is_anime_fan = "Anime" in st.session_state.persona.get("content_type", "")
        
        with st.spinner(""):
            if gemini_available:
                # Customize prompt based on collected data
                content_preference = st.session_state.persona.get("content_type", "")
                genre_preference = st.session_state.persona.get("preferred_genres", "")
                mood = st.session_state.mood_context.get("current_mood", "")
                
                prompt = f"""
                Based on this user persona: {persona_json}
                And their current mood/context: {mood_json}
                
                The user prefers {content_preference} and enjoys {genre_preference} genres. 
                They are currently feeling {mood}.
                
                Recommend exactly 3 {'anime series or movies' if is_anime_fan else 'movies or shows'} that would perfectly match these preferences.
                
                For each recommendation, provide:
                1. Title (exact spelling is important)
                2. Year of release (if known)
                3. Type (movie, TV show, or anime)
                4. A brief explanation of why this would appeal to this specific user based on their preferences and current mood

                Return the response in this JSON format ONLY:
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
                The response must be valid JSON and nothing else.
                """
                
                try:
                    response_text = call_gemini_api(prompt)
                    if response_text:
                        # Find JSON in the response
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = response_text[json_start:json_end]
                            try:
                                recommendations_data = json.loads(json_str)
                            except json.JSONDecodeError as e:
                                pass
                except Exception as e:
                    pass
            else:
                # If Gemini API is not available, use fallback recommendations that match persona
                if is_anime_fan:
                    recommendations_data = {
                        "recommendations": [
                            {
                                "title": "My Hero Academia",
                                "year": "2016",
                                "type": "anime",
                                "explanation": "A popular anime about superheroes with great action and character development."
                            },
                            {
                                "title": "Your Name",
                                "year": "2016",
                                "type": "anime",
                                "explanation": "A beautiful anime film with stunning visuals and an emotional story."
                            },
                            {
                                "title": "Attack on Titan",
                                "year": "2013",
                                "type": "anime",
                                "explanation": "An intense, dark anime with incredible action sequences and a gripping plot."
                            }
                        ]
                    }
        
        # Process each recommendation and get details from TMDB
        processed_recommendations = []
        
        for rec in recommendations_data["recommendations"]:
            # Determine media type for API
            media_type = "movie"
            if rec["type"].lower() in ["show", "tv show", "tv", "series"]:
                media_type = "tv"
            elif rec["type"].lower() == "anime":
                media_type = "tv"  # Most anime are categorized as TV shows in TMDB
            
            # Search for the title with enhanced handling for anime
            search_results = search_movies(rec["title"], media_type)
            
            if search_results and search_results.get("results", []):
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
                        "year": details.get("release_date", details.get("first_air_date", rec.get("year", ""))),
                        "overview": details.get("overview", "Details not available."),
                        "image_url": image_url,
                        "explanation": rec["explanation"],
                        "media_type": media_type,
                        "genres": [genre["name"] for genre in details.get("genres", [])] or ["N/A"]
                    }
                    
                    processed_recommendations.append(recommendation)
                else:
                    # Create a basic recommendation with the search result data
                    poster_path = result.get("poster_path")
                    base_url = st.session_state.tmdb_config["images"]["secure_base_url"]
                    poster_size = st.session_state.tmdb_config["images"]["poster_sizes"][3]
                    image_url = get_image_url(poster_path, base_url, poster_size)
                    
                    recommendation = {
                        "id": movie_id,
                        "title": result.get("title", result.get("name", rec["title"])),
                        "year": result.get("release_date", result.get("first_air_date", rec.get("year", ""))),
                        "overview": result.get("overview", "Details not available."),
                        "image_url": image_url,
                        "explanation": rec["explanation"],
                        "media_type": media_type,
                        "genres": ["N/A"]  # We don't have genre information from search
                    }
                    
                    processed_recommendations.append(recommendation)
            else:
                # If TMDB search fails, create a basic recommendation with fallback image
                recommendation = {
                    "id": 0,
                    "title": rec["title"],
                    "year": rec.get("year", ""),
                    "overview": "Details not available from our database, but this is a great match for your preferences!",
                    "image_url": "https://i.ibb.co/s9ZYS5wk/45e6544ed099.jpg",  # Use provided fallback image
                    "explanation": rec["explanation"],
                    "media_type": rec["type"].lower(),
                    "genres": ["N/A"]
                }
                processed_recommendations.append(recommendation)
        
        st.session_state.recommendations = processed_recommendations
        st.session_state.stage = 'results'
        st.rerun()
    
    # STAGE 4: Display Recommendations
    elif st.session_state.stage == 'results':
        if not st.session_state.recommendations:
            st.warning("We couldn't find recommendations that match your preferences. Please try again.")
            if st.button("Start Over"):
                # Reset session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        else:
            # Display recommendations in enhanced cards
            cols = st.columns(len(st.session_state.recommendations))
            
            for i, rec in enumerate(st.session_state.recommendations):
                with cols[i]:
                    st.markdown(f"""
                    <div class='recommendation-card'>
                        <h3>{rec['title']}</h3>
                        <p><strong>Year:</strong> {rec['year'][:4] if rec['year'] else 'N/A'}</p>
                        <img src="{rec['image_url']}" alt="{rec['title']}" style="width:100%; border-radius:5px; margin:10px 0;">
                        <p><strong>Genres:</strong> {', '.join(rec['genres']) if rec['genres'] else 'N/A'}</p>
                        <div style="margin-top:15px; padding:15px; border-left: 2px solid #8a2be2;">
                            <p><strong>Why we recommend this:</strong> {rec['explanation']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Restart button with enhanced styling
            if st.button("Start Over"):
                # Reset session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
                
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
                <img src="https://www.gstatic.com/gumdrop/files/bard-gemini-word-mark-transparent-w312px-h112px-2x.png" 
                     alt="Google Gemini" width="120">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
