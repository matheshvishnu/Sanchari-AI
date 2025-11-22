import streamlit as st
import requests
import re

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Sanchari AI", 
    page_icon="🌍",
    layout="centered"
)

# Define headers globally to use across functions
HEADERS = {'User-Agent': 'SanchariAI/1.0'}

# --- CACHED FUNCTIONS (API HANDLERS) ---
# We move API calls outside the class and decorate them to prevent
# the bot from re-running expensive network calls on every interaction.

@st.cache_data(ttl=3600) # Cache data for 1 hour
def get_coordinates(place):
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': place, 'format': 'json', 'limit': 1}
    try:
        # Added timeout to prevent hanging indefinitely
        response = requests.get(url, headers=HEADERS, params=params, timeout=5)
        data = response.json()
        if data:
            return {
                'lat': data[0]['lat'],
                'lon': data[0]['lon'],
                'name': data[0]['display_name']
            }
        return None
    except Exception as e:
        print(f"Error fetching coordinates: {e}")
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
    except Exception as e:
        print(f"Error fetching weather: {e}")
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
        # CRITICAL FIX: Added headers here so Overpass doesn't block us
        response = requests.get(url, params={'data': query}, headers=HEADERS, timeout=25)
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
    except Exception as e:
        print(f"Error fetching places: {e}")
        return []

# --- MAIN LOGIC CLASS ---

class TourismMultiAgentSystem:
    def __init__(self):
        pass

    def parent_agent(self, user_input):
        city = None
        user_input_lower = user_input.lower()
        
        # 1. Try to find city using "visit [city]" or "weather in [city]" pattern
        match = re.search(r"(?:go to|visit|in|trip to|weather of|weather for)\s+([a-zA-Z\s]+?)(?:,|$|\slet|\swhat|\?)", user_input_lower)
        
        if match:
            city = match.group(1).strip()
        else:
            # 2. Fallback: Find a likely city name by ignoring common words
            ignored_words = [
                "i", "i'm", "im", "what", "where", "tell", "me", "weather", 
                "is", "the", "how", "a", "places", "visit", "plan", "trip", "to", "for", "of"
            ]
            words = user_input.split()
            for w in words:
                clean_w = w.strip("?,.!").lower()
                # If the word is not common and has decent length, assume it's the city
                if clean_w not in ignored_words and len(clean_w) > 2:
                    city = clean_w
                    break
        
        if not city:
            return "I'm sorry, I couldn't understand which city you want to visit. Please try saying 'Weather in Goa' or 'Visit Paris'."
        
        # Call the cached function
        loc_data = get_coordinates(city)
        
        if not loc_data:
            return f"I couldn't find a place named '{city}'. Please check the spelling."
            
        weather_keywords = ['weather', 'whether', 'temperature', 'rain', 'hot', 'cold', 'climate']
        wants_weather = any(x in user_input_lower for x in weather_keywords)
        
        places_keywords = ['place', 'visit', 'attraction', 'trip', 'plan', 'see', 'spot']
        wants_places = any(x in user_input_lower for x in places_keywords)
        
        # Default behavior: if they just say a city name, give them places
        if not wants_weather and not wants_places:
            wants_places = True
            
        lat, lon = loc_data['lat'], loc_data['lon']
        display_city = loc_data['name'].split(',')[0] # Cleaner display name
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
                output_parts.append(f"I looked for attractions near {display_city} but didn't find specifically tagged tourist spots in my database.")

        return "\n\n".join(output_parts)

# --- STREAMLIT UI ---

st.title("🌍 Sanchari AI")
st.markdown("I can help you check the **Weather** ⛅ and find **Places to Visit** 🏛️.")

# Initialize Session State
if 'agent' not in st.session_state:
    st.session_state.agent = TourismMultiAgentSystem()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Hello! Where would you like to go today?"})

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Type your travel plans here..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        response_text = st.session_state.agent.parent_agent(prompt)

    with st.chat_message("assistant"):
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
