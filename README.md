<div align="center">

# Sanchari AI: Multi-Agent Tourism System

**An AI-driven travel assistant developed for AI Intern Assignment.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Framework-Streamlit-red)](https://streamlit.io/)
[![Status](https://img.shields.io/badge/Status-Completed-success)](https://sanchari-ai.streamlit.app/)

</div>

---

## Project Overview

Sanchari AI is a Multi-Agent System designed to act as a tourism assistant. The system interprets natural language inputs to determine user intent and orchestrates child agents to fetch real-time data from external APIs.

The project adheres to the **Inkle AI Intern Assignment** requirements by implementing a Parent Agent that coordinates two specific Child Agents: a Weather Agent and a Places Agent.

---

## Problem Statement & Solution

**Objective:** Build a multi-agent tourism system that accepts a user's destination and provides weather forecasts and tourist attractions based on the query context.

**Architecture:**
The system utilizes a **Hub-and-Spoke architecture**:

1.  **Parent Agent (Orchestrator):**
    * Parses user input using Regex and heuristic logic.
    * Determines if the user requires weather data, tourist locations, or both.
    * Handles error cases for non-existent locations.
2.  **Geolocation Service (Helper):**
    * Utilizes the **Nominatim API** to convert city names into latitude and longitude.
3.  **Child Agent 1: Weather Agent:**
    * Fetches current temperature and precipitation probability using the **Open-Meteo API**.
4.  **Child Agent 2: Places Agent:**
    * Queries the **Overpass API (OpenStreetMap)** to identify nodes tagged as `tourism=attraction` within a specific radius.

---

## API Integration

This system operates without relying on Large Language Model (LLM) internal knowledge for facts. Instead, it strictly fetches real-time data from the following open-source APIs:

| Component | API Provider | Endpoint / Usage |
| :--- | :--- | :--- |
| **Geocoding** | Nominatim API | `https://nominatim.openstreetmap.org/search` |
| **Weather** | Open-Meteo API | `https://api.open-meteo.com/v1/forecast` |
| **Attractions** | Overpass API | `https://overpass-api.de/api/interpreter` |

---

## Getting Started

<h3>Option 1: Local Installation</h3>
<ol>
  <li><strong>Clone the repository:</strong>
    <pre><code>git clone https://github.com/matheshvishnu/sanchari-ai.git
cd sanchari-ai</code></pre>
  </li>
  <li><strong>Install dependencies:</strong>
    <pre><code>pip install -r requirements.txt</code></pre>
  </li>
  <li><strong>Run the App:</strong>
    <pre><code>streamlit run app.py</code></pre>
  </li>
</ol>

<hr>

## Project Structure
<pre>
├── main.py              # Local development script
├── app.py               # Main web application & UI logic
└── requirements.txt     # Project dependencies
</pre>

<hr>

## Usage Examples

<h3>Example 1: Planning a Trip</h3>

<blockquote>
<strong>Input:</strong> "I’m going to go to Bangalore, let’s plan my trip."
</blockquote>

<p><strong>Output:</strong></p>

<pre>
In Bangalore these are the places you can go,

Lalbagh

Sri Chamarajendra Park

Bangalore Palace

Bannerghatta National Park

Jawaharlal Nehru Planetarium
</pre>

<h3>Example 2: Checking Weather</h3>

<blockquote>
<strong>Input:</strong> "What is the weather in London?"
</blockquote>

<p><strong>Output:</strong></p>

<pre>
In London it’s currently 12°C with a chance of 40% to rain.
</pre>

<h3>Example 3: Full Itinerary</h3>

<blockquote>
<strong>Input:</strong> "I want to visit Paris, tell me the weather and places to see."
</blockquote>

<p><strong>Output:</strong></p>

<pre>
In Paris it’s currently 18°C with a chance of 10% to rain.
And these are the places you can go:

Eiffel Tower

Louvre Museum

Notre Dame

Arc de Triomphe

Sacré-Cœur
</pre>

<hr>

## Clone Repository
Not adding as this is made for the assignment purpose of my Online assesment for AI intern

## Future Scope

<ul>
<li><strong>LLM Integration:</strong> Replace Regex with OpenAI/Gemini API for advanced conversational capabilities.</li>
<li><strong>Route Optimization:</strong> Suggest the best route to visit the selected places.</li>
<li><strong>Hotel & Flight Booking:</strong> Integrate Booking.com or Skyscanner APIs.</li>
</ul>

<hr>

## Author

<p><strong>V Mathesh</strong></p>
<ul>
<li><a href="https://www.linkedin.com/in/matheshv/">LinkedIn</a></li>
<li><a href="https://github.com/matheshvishnu">GitHub</a></li>
</ul>
