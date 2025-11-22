import streamlit as st
import requests
import re

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Sanchari AI", 
    page_icon="🌍",
    layout="centered"
)

# CRITICAL FIX: Nominatim requires an email in the User-Agent to identify the developer.
# If you don't add this, they will block your requests (403 Forbidden).
HEADERS = {
    'User-Agent': 'SanchariAI_StudentProject/1.0 (your_email@example.com)', 
    'Referer': 'https://sanchari-ai.streamlit.app/'
}

# --- CACHED FUNCTIONS (API HANDLERS) ---

@st.cache_data(ttl=3600)
def get_coordinates(place):
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': place, 'format': 'json', 'limit': 1}
    try:
        # Added timeout and specific headers
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        
        # DEBUGGING: If it fails, this will show why in the app
        if response.status_code != 200:
            st.error(f"❌ Map Error: {response.status_code} (Reason: {response.reason})")
            return None
            
        data = response.json()
        if data:
            return {
                'lat': data[0]['lat'],
                'lon': data[0]['lon'],
                'name': data[0]['display_name']
            }
        return None
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return None

@st.cache_data(ttl=3600)
def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,precipitation_probability"
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        current = data.get('current', {})
        temp = current.get('temperature_2m', 'N/A')
        rain = current.get('precipitation_probability', 0)
        return f"currently {temp}°C with a chance of {rain}% to rain"
    except:
        return "weather info unavailable"

@st.cache_data(ttl=3600)
def get_places(lat, lon):
    url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    node["tourism"="attraction"](around:20000, {lat}, {lon});
    out 20;
    """
    try:
        # Added headers here too to prevent Overpass blocking
        response = requests.get(url, params={'data': query}, headers=HEADERS, timeout=25)
        if response.status_code != 200:
            st.error(f"❌ Places Error: {response.status_code}")
            return []
            
        data = response.json()
        elements = data.get('elements', [])
        
        valid_places = []
        seen_names = set()
        for item in elements:
            name = item.get('tags', {}).get('name')
            if name and name not in seen_names:
                valid_places.append(name)
                seen_names.add(name)
        return valid_places[:5]
    except:
        return []

# --- MAIN LOGIC CLASS ---

class TourismMultiAgentSystem:
    def __init__(self):
        pass

    def parent_agent(self, user_input):
        city = None
        user_input_lower = user_input.lower()
        
        # 1. Regex Extraction
        match = re.search(r"(?:go to|visit|in|trip to|weather of|weather for)\s+([a-zA-Z\s]+?)(?:,|$|\slet|\swhat|\?)", user_input_lower)
        if match:
            city = match.group(1).strip()
        else:
            # 2. Smart Fallback
            ignored_words = [
                "i", "i'm", "im", "what", "where", "tell", "me", "weather", 
                "is", "the", "how", "a", "places", "visit", "plan", "trip", "to", "for", "of"
            ]
            words = user_input.split()
            for w in words:
                clean_w = w.strip("?,.!").lower()
                if clean_w not in ignored_words and len(clean_w) > 2:
                    city = clean_w
                    break
        
        if not city:
            return "I'm sorry, I couldn't understand which city you want to visit. Please try saying 'Weather in Goa' or 'Visit Paris'."
        
        # Get Coordinates
        loc_data = get_coordinates(city)
        
        if not loc_data:
            # Return a specific help message if city not found
            return f"I searched for '{city}' but couldn't find it on the map. Please check the spelling."
            
        # Determine User Intent
        weather_keywords = ['weather', 'whether', 'temperature', 'rain', 'hot', 'cold', 'climate']
        wants_weather = any(x in user_input_lower for x in weather_keywords)
        
        places_keywords = ['place', 'visit', 'attraction', 'trip', 'plan', 'see', 'spot']
        wants_places = any(x in user_input_lower for x in places_keywords)
        
        if not wants_weather and not wants_places:
            wants_places = True
            
        lat, lon = loc_data['lat'], loc_data['lon']
        display_city = loc_data['name'].split(',')[0]
        output_parts = []

        if wants_weather:
            weather_info = get_weather(lat, lon)
            output_parts.append(f"In {display_city} it’s {weather_info}.")

        if wants_places:
            attractions = get_places(lat, lon)
            if attractions:
                intro = "And these" if wants_weather else f"In {display_city}, these"
                places_str = "\n".join([f"- {p}" for p in attractions])
                output_parts.append(f"{intro} are the top places you can visit:\n{places_str}")
            else:
                output_parts.append(f"I found {display_city}, but I couldn't retrieve specific tourist spots right now.")

        return "\n\n".join(output_parts)

# --- STREAMLIT UI ---

st.title("🌍 Sanchari AI")
st.markdown("I can help you check the **Weather** ⛅ and find **Places to Visit** 🏛️.")

if 'agent' not in st.session_state:
    st.session_state.agent = TourismMultiAgentSystem()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Hello! Where would you like to go today?"})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type your travel plans here..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        response_text = st.session_state.agent.parent_agent(prompt)

    with st.chat_message("assistant"):
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
