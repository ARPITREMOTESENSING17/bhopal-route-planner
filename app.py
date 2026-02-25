import streamlit as st
import folium
import osmnx as ox
from geopy.geocoders import Nominatim
from streamlit_folium import folium_static
import time

# Page config
st.set_page_config(
    page_title="Bhopal Route Planner",
    page_icon="🗺️",
    layout="wide"
)

# Title
st.title("🗺️ Bhopal Route Planner")
st.markdown("Select or enter any two locations in Bhopal to find the shortest route!")

# Popular Bhopal locations
POPULAR_LOCATIONS = [
    "Custom Location (Type Below)",
    "MANIT Bhopal",
    "Bhopal Railway Station",
    "DB Mall",
    "Van Vihar National Park",
    "Upper Lake",
    "Lower Lake",
    "Taj-ul-Masajid",
    "MP Nagar",
    "New Market",
    "Rani Kamlapati Railway Station",
    "Raja Bhoj Airport",
    "AIIMS Bhopal",
    "Bharat Bhavan",
    "Birla Mandir",
    "Shaukat Mahal",
    "TT Nagar",
    "Arera Colony",
    "Shahpura",
    "Kolar",
    "Bairagarh",
    "BHEL Bhopal",
    "Nehru Nagar",
    "Bittan Market",
    "Chowk Bazaar"
]

# Manual coordinates for locations that Nominatim struggles with
LOCATION_COORDINATES = {
    "Bharat Bhavan": (23.2380, 77.4092),
    "Birla Mandir": (23.2367, 77.4015),
    "Upper Lake": (23.2494, 77.3897),
    "Lower Lake": (23.2386, 77.4127),
    "Bittan Market": (23.2599, 77.4126),
    "Chowk Bazaar": (23.2645, 77.4088),
}

# Cache road network
@st.cache_resource
def load_graph():
    with st.spinner("Loading Bhopal road network... (first time only)"):
        G = ox.graph_from_place('Bhopal, India', network_type='drive')
    return G

# Improved geocode function with fallback
def geocode(place):
    # Check manual coordinates first
    if place in LOCATION_COORDINATES:
        class ManualLocation:
            def __init__(self, lat, lon, name):
                self.latitude = lat
                self.longitude = lon
                self.address = name
        
        coords = LOCATION_COORDINATES[place]
        return ManualLocation(coords[0], coords[1], place)
    
    # Try Nominatim with multiple variations
    geolocator = Nominatim(user_agent="bhopal_route_app_v2")
    
    search_variations = [
        f"{place}, Bhopal, Madhya Pradesh, India",
        f"{place}, Bhopal, India",
        f"{place}, Bhopal",
        place
    ]
    
    for search_term in search_variations:
        try:
            time.sleep(1)  # Respect Nominatim rate limits
            location = geolocator.geocode(search_term, timeout=10)
            if location:
                return location
        except Exception as e:
            continue
    
    return None

# Load graph
G = load_graph()

# Input section with dropdowns
col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Start Location")
    start_dropdown = st.selectbox(
        "Choose from popular locations:",
        POPULAR_LOCATIONS,
        key="start_select"
    )
    
    if start_dropdown == "Custom Location (Type Below)":
        start_name = st.text_input(
            "Enter custom start location:",
            placeholder="e.g. Roshanpura",
            key="start_input"
        )
    else:
        start_name = start_dropdown

with col2:
    st.subheader("🏁 End Location")
    end_dropdown = st.selectbox(
        "Choose from popular locations:",
        POPULAR_LOCATIONS,
        key="end_select"
    )
    
    if end_dropdown == "Custom Location (Type Below)":
        end_name = st.text_input(
            "Enter custom end location:",
            placeholder="e.g. Piplani",
            key="end_input"
        )
    else:
        end_name = end_dropdown

# Calculate button
if st.button("🚗 Find Route", type="primary"):
    if start_name and end_name and start_name != "Custom Location (Type Below)" and end_name != "Custom Location (Type Below)":
        with st.spinner("Calculating route..."):

            # Geocode locations
            start = geocode(start_name)
            end   = geocode(end_name)

            if start and end:
                # Find nearest nodes
                orig_node = ox.distance.nearest_nodes(G, start.longitude, start.latitude)
                dest_node = ox.distance.nearest_nodes(G, end.longitude, end.latitude)

                # Calculate route
                route = ox.shortest_path(G, orig_node, dest_node, weight='length')

                if route:
                    # Calculate distance
                    route_edges  = ox.routing.route_to_gdf(G, route, weight='length')
                    route_length = route_edges['length'].sum()
                    travel_time  = (route_length/1000) / 40 * 60

                    # Show stats
                    c1, c2, c3 = st.columns(3)
                    c1.metric("📍 From", start_name)
                    c2.metric("📏 Distance", f"{route_length/1000:.2f} km")
                    c3.metric("⏱️ Time (40km/h)", f"{travel_time:.0f} mins")

                    # Create map
                    center_lat = (start.latitude + end.latitude) / 2
                    center_lon = (start.longitude + end.longitude) / 2
                    m = folium.Map(
                        location=[center_lat, center_lon],
                        zoom_start=13,
                        tiles='OpenStreetMap'
                    )

                    # Route coordinates
                    route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]

                    # Add route line
                    folium.PolyLine(
                        locations=route_coords,
                        color='red',
                        weight=5,
                        opacity=0.8
                    ).add_to(m)

                    # Start marker
                    folium.Marker(
                        location=[start.latitude, start.longitude],
                        popup=f"START: {start_name}",
                        icon=folium.Icon(color='green', icon='play', prefix='fa')
                    ).add_to(m)

                    # End marker
                    folium.Marker(
                        location=[end.latitude, end.longitude],
                        popup=f"END: {end_name}",
                        icon=folium.Icon(color='red', icon='flag', prefix='fa')
                    ).add_to(m)

                    # Display map
                    folium_static(m, width=1200, height=500)

                else:
                    st.error("❌ No route found between these locations!")
            else:
                if not start:
                    st.error(f"❌ Could not find '{start_name}'. Try a different name or use Custom Location.")
                if not end:
                    st.error(f"❌ Could not find '{end_name}'. Try a different name or use Custom Location.")
    else:
        st.warning("⚠️ Please select or enter both start and end locations!")

