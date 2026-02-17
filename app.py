import streamlit as st
import folium
import osmnx as ox
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

# Page config
st.set_page_config(
    page_title="Bhopal Route Planner",
    page_icon="🗺️",
    layout="wide"
)

# Title
st.title("🗺️ Bhopal Route Planner")
st.markdown("Enter any two locations in Bhopal to find the shortest route!")

# Cache road network
@st.cache_resource
def load_graph():
    with st.spinner("Loading Bhopal road network... (first time only)"):
        G = ox.graph_from_place('Bhopal, India', network_type='drive')
    return G

# Geocode function
def geocode(place):
    geolocator = Nominatim(user_agent="bhopal_route_app")
    location = geolocator.geocode(f"{place}, Bhopal, India")
    return location

# Load graph
G = load_graph()

# Input section
col1, col2 = st.columns(2)
with col1:
    start_name = st.text_input("📍 Start Location", placeholder="e.g. MANIT Bhopal")
with col2:
    end_name = st.text_input("🏁 End Location", placeholder="e.g. DB Mall")

# Calculate button
if st.button("🚗 Find Route", type="primary"):
    if start_name and end_name:
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
                        popup=folium.Popup(f"START: {start_name}", parse_html=False),
                        icon=folium.Icon(color='green')
                    ).add_to(m)

                    # End marker
                    folium.Marker(
                        location=[end.latitude, end.longitude],
                        popup=folium.Popup(f"END: {end_name}", parse_html=False),
                        icon=folium.Icon(color='red')
                    ).add_to(m)

                    # Display map
                    map_html = m._repr_html_()
                    st.components.v1.html(map_html, width=1200, height=500)

                else:
                    st.error("❌ No route found!")
            else:
                st.error("❌ Could not find locations. Try different names!")
    else:
        st.warning("⚠️ Please enter both locations!")