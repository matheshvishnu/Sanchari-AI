import streamlit as st
import requests
import re

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Sanchari AI", 
    page_icon="🌍",
    layout="centered"
)

# Headers to look like a legitimate browser/app
HEADERS = {
    'User-Agent': 'SanchariAI_StudentProject/1.0', 
    'Accept': 'application/json'
}

# --- CACHED API FUNCTIONS ---

@st.cache_data(ttl=3600)
def get_coordinates(place):
    """
    Uses Photon API (Komoot) instead of Nominatim.
    Photon is faster and does not block Streamlit Cloud IPs.
    """
    url = "https://photon.komoot.io/api/"
    params = {'q': place, 'limit': 1}
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = response.json()
        
        if data and 'features' in data and len(data['features']) > 0:
            # Photon returns coordinates in [Longitude, Latitude] order
            coords = data['features'][0]['geometry']['coordinates']
            props = data['features'][0]['properties']
            
            return {
                'lon': coords[0],
                'lat': coords[1],
                'name': props.get('name', place),
                'country': props.get('country', '')
            }
        return None
    except Exception as e:
        print(f"Map Error: {e}")
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
        return f"{temp}°C with a {rain}% chance of rain"
    except:
        return "weather info unavailable"

@st.cache_data(ttl=3600)
def get_places(lat, lon):
    url = "https://overpass-api.de/api/interpreter"
    # Reduced radius to 5000m (5km) and limit to 10 for faster response
    query = f"""
    [out:json];
    node["tourism"="attraction"](around:5000, {lat}, {lon});
    out 10;
    """
    try:
        response = requests.get(url, params={'data': query}, headers=HEADERS, timeout=20)
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

# --- AGENT LOGIC ---

class TourismMultiAgentSystem:
    def __init__(self):
        pass

    def parent_agent(self, user_input):
        city = None
        user_input_lower = user_input.lower()
        
        # 1. Regex Extraction (Updated for "Travel to", "Want to")
        patterns = [
            r"(?:go to|travel to|visit|in|trip to|weather of|weather for)\s+([a-zA-Z\s]+)",
            r"(?:places|attractions|spots)\s+(?:in|near|at)\s+([a-zA-Z\s]+)"
        ]
        
        for p in patterns:
            match = re.search(p, user_input_lower)
            if match:
                city = match.group(1).strip()
                break
        
        # 2. Fallback: Smart Word Filtering
        if not city:
            # Words to ignore so we can find the city name
            ignored_words = [
                "i", "i'm", "im", "want", "would", "like", "to", "go", "travel", "visit", 
                "what", "where", "tell", "me", "show", "weather", "is", "the", "how", 
                "a", "places", "plan", "trip", "for", "of", "suggest", "some", "few"
            ]
            words = user_input.split()
            for w in words:
                clean_w = w.strip("?,.!").lower()
                if clean_w not in ignored_words and len(clean_w) > 2:
                    city = clean_w
                    break
        
        if not city:
            return "I'm sorry, I couldn't understand which city you want to visit. Try typing just the city name, like 'London'."
        
        # Get Coordinates (Using Photon)
        loc_data = get_coordinates(city)
        
        if not loc_data:
            return f"I searched for '{city}' but couldn't find it on the map. Please check the spelling."
            
        # Intent Detection
        weather_keywords = ['weather', 'whether', 'temperature', 'rain', 'hot', 'cold', 'climate']
        wants_weather = any(x in user_input_lower for x in weather_keywords)
        
        places_keywords = ['place', 'visit', 'attraction', 'trip', 'plan', 'see', 'spot']
        wants_places = any(x in user_input_lower for x in places_keywords)
        
        # Default to places if no specific intent
        if not wants_weather and not wants_places:
            wants_places = True
            
        lat, lon = loc_data['lat'], loc_data['lon']
        display_name = loc_data['name']
        country = loc_data['country']
        full_location = f"{display_name}, {country}" if country else display_name
        
        output_parts = []

        if wants_weather:
            weather_info = get_weather(lat, lon)
            output_parts.append(f"**Weather in {full_location}:**\nIt is {weather_info}.")

        if wants_places:
            attractions = get_places(lat, lon)
            if attractions:
                intro = "\n**Nearby Attractions:**"
                places_str = "\n".join([f"🏛️ {p}" for p in attractions])
                output_parts.append(f"{intro}\n{places_str}")
            else:
                output_parts.append(f"\nI found the location ({full_location}), but could not find specific tagged tourist attractions nearby in the database.")

        return "\n".join(output_parts)

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

    with st.spinner(f"Checking travel info for {prompt}..."):
        response_text = st.session_state.agent.parent_agent(prompt)

    with st.chat_message("assistant"):
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
