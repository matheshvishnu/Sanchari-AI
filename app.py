import streamlit as st
import requests
import re
class TourismMultiAgentSystem:
    def __init__(self):
        self.headers = {'User-Agent': 'SanchariAI/1.0'}

    def get_coordinates(self, place):
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': place, 'format': 'json', 'limit': 1}
        try:
            response = requests.get(url, headers=self.headers, params=params)
            data = response.json()
            if data:
                return {
                    'lat': data[0]['lat'],
                    'lon': data[0]['lon'],
                    'name': data[0]['display_name']
                }
            return None
        except:
            return None

    def weather_agent(self, lat, lon):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,precipitation_probability"
        }
        try:
            response = requests.get(url, params=params)
            data = response.json()
            current = data.get('current', {})
            temp = current.get('temperature_2m', 'N/A')
            rain = current.get('precipitation_probability', 0)
            return f"currently {temp}°C with a chance of {rain}% to rain"
        except:
            return "weather info unavailable"

    def places_agent(self, lat, lon):
        url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        node["tourism"="attraction"](around:20000, {lat}, {lon});
        out 20;
        """
        try:
            response = requests.get(url, params={'data': query})
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

    def parent_agent(self, user_input):
        city = None
        user_input_lower = user_input.lower()
        match = re.search(r"(?:go to|visit|in|trip to)\s+([a-zA-Z\s]+?)(?:,|$|\slet|\swhat|\?)", user_input_lower)
        
        if match:
            city = match.group(1).strip()
        else:
            words = user_input.split()
            for w in words:
                clean_w = w.strip("?,.")
                if clean_w[0].isupper() and clean_w.lower() not in ["i", "i'm", "what", "where", "tell", "me"]:
                    city = clean_w
                    break
        
        if not city:
            return "I'm sorry, I couldn't understand which city you want to visit."
        loc_data = self.get_coordinates(city)
        if not loc_data:
            return "It doesn’t know this place exist"
        weather_keywords = ['weather', 'whether', 'temperature', 'rain', 'hot', 'cold', 'climate']
        wants_weather = any(x in user_input_lower for x in weather_keywords)
        
        places_keywords = ['place', 'visit', 'attraction', 'trip', 'plan', 'see']
        wants_places = any(x in user_input_lower for x in places_keywords)
        
        if not wants_weather and not wants_places:
            wants_places = True
        lat, lon = loc_data['lat'], loc_data['lon']
        display_city = city.title()
        output_parts = []

        if wants_weather:
            weather_info = self.weather_agent(lat, lon)
            output_parts.append(f"In {display_city} it’s {weather_info}.")

        if wants_places:
            attractions = self.places_agent(lat, lon)
            if attractions:
                intro = "And these" if wants_weather else f"In {display_city} these"
                places_str = "\n".join([f"- {p}" for p in attractions])
                output_parts.append(f"{intro} are the places you can go:\n{places_str}")
            else:
                output_parts.append(f"I couldn't find specific tourist attractions nearby {display_city} (OpenStreetMap data might be sparse here).")

        return " ".join(output_parts)

st.set_page_config(page_title="Sanchari AI", page_icon="🌍")

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
