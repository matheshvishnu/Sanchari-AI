import streamlit as st
import requests
import re

# =================================================================================
# Tourism Multi-Agent System
# =================================================================================
class TourismMultiAgentSystem:
    def __init__(self):
        self.headers = {'User-Agent': 'SanchariAI/1.0'}

    # ===================== Get Coordinates ===================== #
    def get_coordinates(self, place):
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': place, 'format': 'json', 'limit': 1}
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=12)
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

    # ===================== Weather Agent ===================== #
    def weather_agent(self, lat, lon):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,precipitation_probability"
        }
        try:
            response = requests.get(url, params=params, timeout=12)
            data = response.json()
            current = data.get('current', {})
            temp = current.get('temperature_2m', 'N/A')
            rain = current.get('precipitation_probability', 0)
            return f"currently {temp}°C with a chance of {rain}% rain"
        except:
            return "weather info unavailable"

    # ===================== Places Agent ===================== #
    def places_agent(self, lat, lon):
        url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        node["tourism"="attraction"](around:15000, {lat}, {lon});
        out 20;
        """
        try:
            response = requests.get(url, params={'data': query}, headers=self.headers, timeout=15)
            data = response.json()
            elements = data.get('elements', [])
            valid_places = []

            seen = set()
            for item in elements:
                name = item.get('tags', {}).get('name')
                if name and name not in seen:
                    valid_places.append(name)
                    seen.add(name)
            return valid_places[:6]
        except:
            return []

    # ===================== Parent Agent ===================== #
    def parent_agent(self, user_input):
        text = user_input.lower()
        city = None

        # 👇 MORE FLEXIBLE TRAVEL PATTERNS
        patterns = [
            r"go to ([a-zA-Z\s]+)",
            r"visit ([a-zA-Z\s]+)",
            r"travel to ([a-zA-Z\s]+)",
            r"trip to ([a-zA-Z\s]+)",
            r"in ([a-zA-Z\s]+)",
            r"to ([a-zA-Z\s]+)"
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                city = match.group(1).strip()
                break

        # 👇 Fallback — last noun-like word (for inputs like "London", "Australia")
        if not city:
            words = user_input.split()
            for w in reversed(words):
                w_clean = w.strip("?,.")
                if w_clean.isalpha() and len(w_clean) > 2:
                    city = w_clean
                    break

        # If still unknown
        if not city:
            return "I'm sorry, I couldn't understand which city you meant. Try: *London*, *Australia*, *Paris*, etc."

        loc_data = self.get_coordinates(city)
        if not loc_data:
            return f"I couldn't find this place **{city}**. Check spelling once."

        lat, lon = loc_data["lat"], loc_data["lon"]
        display_city = city.title()

        wants_weather = any(x in text for x in ['weather', 'temperature', 'rain', 'climate'])
        wants_places = any(x in text for x in ['place', 'visit', 'trip', 'attraction', 'plan', 'see'])

        # If user just sends city name → send both details
        if not wants_weather and not wants_places:
            wants_weather = True
            wants_places = True

        reply = []

        # Weather
        if wants_weather:
            weather_info = self.weather_agent(lat, lon)
            reply.append(f"📍 **{display_city}** — Weather is {weather_info}.")

        # Places
        if wants_places:
            attractions = self.places_agent(lat, lon)
            if attractions:
                places = "\n".join([f"• {p}" for p in attractions])
                reply.append(f"🗺️ Top places to visit:\n{places}")
            else:
                reply.append("I couldn’t find popular attractions nearby (OpenStreetMap may not have full data here).")

        return "\n\n".join(reply)

# =================================================================================
# Streamlit UI
# =================================================================================
st.set_page_config(page_title="Sanchari AI", page_icon="🌍")
st.title("🌍 Sanchari AI")
st.markdown("I can help you with **Weather ⛅** and **Places to Visit 🏛️** for any location.")

# Initialize agent
if "agent" not in st.session_state:
    st.session_state.agent = TourismMultiAgentSystem()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Hello! Where would you like to go today? ✨"})

# Show previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# New user input
if prompt := st.chat_input("Type your travel query here..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Exploring the world for you... 🌍"):
        response = st.session_state.agent.parent_agent(prompt)

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
