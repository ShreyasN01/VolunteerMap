"""
Google Maps HTML embed helper for VolunteerMap.

Generates HTML/JavaScript for rendering a Google Maps view with
cluster markers colour-coded by category.
"""

import os
from typing import List, Dict, Any


# Category to color mapping for map markers
CATEGORY_COLORS = {
    "healthcare": "#E53E3E",   # Red
    "food": "#ED8936",         # Orange
    "education": "#3182CE",    # Blue
    "sanitation": "#38A169",   # Green
    "employment": "#805AD5",   # Purple
}

CATEGORY_ICONS = {
    "healthcare": "🏥",
    "food": "🍚",
    "education": "📚",
    "sanitation": "🚿",
    "employment": "💼",
}


def generate_folium_map(clusters: List[Dict[str, Any]], surveys: List[Dict[str, Any]] = None) -> object:
    """
    Generate a Folium map with cluster markers and survey points.

    Args:
        clusters: List of cluster result dictionaries from ML pipeline.
        surveys: Optional list of individual survey entries to show.

    Returns:
        A folium.Map object ready for rendering in Streamlit.
    """
    import folium
    from folium import plugins

    # Centre on Maharashtra
    center_lat = 18.5
    center_lng = 74.0
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=7,
        tiles="CartoDB dark_matter",
        attr="VolunteerMap",
    )

    # Add cluster markers
    for cluster in clusters:
        centroid = cluster.get("centroid", {})
        lat = centroid.get("lat", center_lat)
        lng = centroid.get("lng", center_lng)
        top_category = cluster.get("top_category", "healthcare")
        count = cluster.get("count", 0)
        total_urgency = cluster.get("total_urgency", 0)
        color = CATEGORY_COLORS.get(top_category, "#718096")
        icon_emoji = CATEGORY_ICONS.get(top_category, "📍")

        popup_html = f"""
        <div style="font-family: 'Inter', sans-serif; min-width: 200px;">
            <h4 style="margin: 0 0 8px 0; color: {color};">
                {icon_emoji} Cluster #{cluster.get('cluster_id', 0) + 1}
            </h4>
            <p style="margin: 4px 0;"><strong>Category:</strong> {top_category.title()}</p>
            <p style="margin: 4px 0;"><strong>Needs Count:</strong> {count}</p>
            <p style="margin: 4px 0;"><strong>Total Urgency:</strong> {total_urgency:.1f}</p>
            <p style="margin: 4px 0;"><strong>Avg Urgency:</strong> {(total_urgency / max(count, 1)):.1f}</p>
        </div>
        """

        folium.CircleMarker(
            location=[lat, lng],
            radius=max(8, min(count * 3, 25)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{icon_emoji} {top_category.title()} — {count} needs",
        ).add_to(m)

    # Add individual survey markers if provided
    if surveys:
        marker_cluster = plugins.MarkerCluster(name="Individual Surveys").add_to(m)
        for s in surveys:
            loc = s.get("location", {})
            lat = loc.get("latitude")
            lng = loc.get("longitude")
            if lat and lng:
                cat = s.get("category", "healthcare")
                color = CATEGORY_COLORS.get(cat, "#718096")
                popup_html = f"""
                <div style="font-family: 'Inter', sans-serif;">
                    <p><strong>{cat.title()}</strong> | Severity: {s.get('severity', '?')}</p>
                    <p>{s.get('description', '')[:100]}</p>
                    <p>District: {s.get('district', 'Unknown')}</p>
                    <p>Urgency: {s.get('urgency_score', 0):.1f}</p>
                </div>
                """
                folium.CircleMarker(
                    location=[lat, lng],
                    radius=5,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.5,
                    popup=folium.Popup(popup_html, max_width=250),
                ).add_to(marker_cluster)

    # Add layer control
    folium.LayerControl().add_to(m)

    return m


def generate_map_html(clusters: List[Dict[str, Any]], api_key: str = "") -> str:
    """
    Generate standalone Google Maps HTML embed with cluster markers.

    Args:
        clusters: List of cluster dictionaries.
        api_key: Google Maps JavaScript API key.

    Returns:
        HTML string for embedding in an iframe.
    """
    if not api_key:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")

    markers_js = ""
    for cluster in clusters:
        centroid = cluster.get("centroid", {})
        lat = centroid.get("lat", 18.5)
        lng = centroid.get("lng", 74.0)
        top_category = cluster.get("top_category", "healthcare")
        count = cluster.get("count", 0)
        total_urgency = cluster.get("total_urgency", 0)
        color = CATEGORY_COLORS.get(top_category, "#718096")

        markers_js += f"""
        new google.maps.Marker({{
            position: {{ lat: {lat}, lng: {lng} }},
            map: map,
            title: '{top_category.title()} — {count} needs (Urgency: {total_urgency:.1f})',
            icon: {{
                path: google.maps.SymbolPath.CIRCLE,
                scale: {max(8, min(count * 3, 20))},
                fillColor: '{color}',
                fillOpacity: 0.8,
                strokeWeight: 2,
                strokeColor: '#ffffff',
            }},
        }});
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            #map {{ width: 100%; height: 500px; border-radius: 12px; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            function initMap() {{
                const map = new google.maps.Map(document.getElementById('map'), {{
                    center: {{ lat: 18.5, lng: 74.0 }},
                    zoom: 7,
                    styles: [
                        {{ elementType: 'geometry', stylers: [{{ color: '#1a1a2e' }}] }},
                        {{ elementType: 'labels.text.fill', stylers: [{{ color: '#8a8a8a' }}] }},
                        {{ featureType: 'water', elementType: 'geometry', stylers: [{{ color: '#0f3460' }}] }},
                    ],
                }});
                {markers_js}
            }}
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap" async defer></script>
    </body>
    </html>
    """
    return html
