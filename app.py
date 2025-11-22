import streamlit as st
import requests
import re

st.set_page_config(page_title="Sanchari AI", page_icon="🌍", layout="centered")

HEADERS = {
    'User-Agent': 'SanchariAI_StudentProject/1.0', 
    'Accept': 'application/json'
}

@st.cache_data(ttl=3600)
def get_coordinates(place):
    url = "https://photon.komoot.io/api/"
    params = {'q': place, 'limit': 1}
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = response.json()
        if data and 'features' in data and len(data['features']) > 0:
            coords = data['features'][0]['geometry']['coordinates']
            props = data['features'][0]['properties']
            return {
                'lon': coords[0],
                'lat': coords[1],
                'name': props.get('name', place)
            }
        return None
    except:
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
    node["tourism"="attraction"](around:5000, {lat}, {lon});
    out 10;
    """
    try:
        response = requests.get(url, params={'data': query}, headers=HEADERS, timeout=15)
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

class TourismMultiAgentSystem:
    def __init__(self):
        pass

    def parent_agent(self, user_input):
        city = None
        user_input_lower = user_input.lower()
        
        patterns = [
            r"(?:go to|travel to|visit|in|trip to|plan my trip to)\s+([a-zA-Z\s]+)",
            r"(?:places|attractions)\s+(?:in|near|at)\s+([a-zA-Z\s]+)"
        ]
        
        for p in patterns:
            match = re.search(p, user_input_lower)
            if match:
                city = match.group(1).strip()
                break
        
        if not city:
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
            return "I couldn't understand which city you want to visit."
        
        loc_data = get_coordinates(city)
        
        if not loc_data:
            return f"I couldn't find {city}."
            
        lat, lon = loc_data['lat'], loc_data['lon']
        display_city = loc_data['name']

        weather_keywords = ['weather', 'whether', 'temperature', 'rain', 'hot', 'cold', 'climate']
        wants_weather = any(x in user_input_lower for x in weather_keywords)
        
        places_keywords = ['place', 'visit', 'attraction', 'trip', 'plan', 'see']
        wants_places = any(x in user_input_lower for x in places_keywords)
        
        if not wants_weather and not wants_places:
            wants_places = True
            
        final_response = ""

        if wants_weather:
            weather_info = get_weather(lat, lon)
            final_response += f"In {display_city} it’s {weather_info}.\n\n"

        if wants_places:
            attractions = get_places(lat, lon)
            if attractions:
                if wants_weather:
                    final_response += "And these are the places you can go:\n"
                else:
                    final_response += f"In {display_city} these are the places you can go,\n"
                
                for place in attractions:
                    final_response += f"- {place}\n"
            else:
                final_response += f"\nI couldn't find specific tourist spots in {display_city}."

        return final_response

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
