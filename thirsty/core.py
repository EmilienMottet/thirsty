import io
import math
import re

import folium
import gpxpy
import requests
import rich.console
import rich.progress

console = rich.console.Console()


OVERPASS_URL = "http://overpass-api.de/api/interpreter"


WATER_AMENITIES = {
    "water": "[amenity=drinking_water]",
    "point": "[amenity=water_point][drinking_water=yes]",
    "tap": "[man_made=water_tap][drinking_water=yes]",
    "spring": "[natural=spring][drinking_water=yes]",
    "fountain": "[amenity=fountain][drinking_water=yes]",
}

TOILET_AMENITIES = {
    "toilets": "[amenity=toilets]",
}

REPAIR_AMENITIES = {
    "workshop": "[amenity=bicycle_repair_station]",
    "rental": "[amenity=bicycle_rental]",
    "pump": "[amenity=compressed_air]",
    "shop": "[shop=bicycle]",
}

FOOD_AMENITIES = {
    "cafe": "[amenity=cafe]",
    "restaurant": "[amenity=restaurant]",
    "fast_food": "[amenity=fast_food]",
    "bakery": "[shop=bakery]",
    "supermarket": "[shop=supermarket]",
    "convenience": "[shop=convenience]",
    "greengrocer": "[shop=greengrocer]",
}


def display_gpx_on_map(data, pois):
    """
    Display the GPX route and POIs on a map
    """

    # Create a base map centered around the middle of the GPX track
    track_latitudes = [ point.latitude
                        for track in data.tracks
                        for segment in track.segments
                        for point in segment.points ]

    track_longitudes = [ point.longitude
                         for track in data.tracks
                         for segment in track.segments
                         for point in segment.points ]

    center_lat = sum(track_latitudes) / len(track_latitudes)
    center_lon = sum(track_longitudes) / len(track_longitudes)

    map_center = [center_lat, center_lon]
    folium_map = folium.Map(location=map_center, zoom_start=12)

    # Plot the GPX track on the map
    for track in data.tracks:
        for segment in track.segments:
            # Create a list of coordinates from the GPX track segment
            track_coords = [(point.latitude, point.longitude) for point in segment.points]
            folium.PolyLine(track_coords, color="blue", weight=2.5, opacity=1).add_to(folium_map)

    # Plot POIs on the map
    for poi in pois:
        icon_color = "blue"
        icon_symbol = "info-sign"
        popup_text = ""
        
        if "amenity" in poi["tags"]:
            if poi["tags"]["amenity"] == "toilets":
                icon_color = "purple"
                icon_symbol = "home"
                popup_text = "Toilets"
            elif poi["tags"]["amenity"] == "bicycle_repair_station" or \
                 poi["tags"]["amenity"] == "bicycle_rental" or \
                 poi["tags"]["amenity"] == "compressed_air":
                icon_color = "green"
                icon_symbol = "wrench"
                popup_text = "Bicycle Repair Station"
            elif poi["tags"]["amenity"] in ["cafe", "restaurant", "fast_food"]:
                icon_color = "orange"
                icon_symbol = "cutlery"
                popup_text = f"{poi['tags']['name'] if 'name' in poi['tags'] else poi['tags']['amenity'].capitalize()}"
            else:
                popup_text = f"{poi['tags']['amenity']}"
        elif "shop" in poi["tags"]:
            if poi["tags"]["shop"] == "bicycle":
                icon_color = "green"
                icon_symbol = "wrench"
                popup_text = "Bicycle Shop with Repair"
            elif poi["tags"]["shop"] in ["bakery", "supermarket", "convenience", "greengrocer"]:
                icon_color = "orange"
                icon_symbol = "shopping-cart"
                popup_text = f"{poi['tags']['name'] if 'name' in poi['tags'] else poi['tags']['shop'].capitalize()}"
                
        folium.Marker(
            location=[poi['lat'], poi['lon']],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color=icon_color, icon=icon_symbol)
        ).add_to(folium_map)

    return folium_map


def download_gpx(url):
    """
    Download GPX from URL
    """

    console.print(f"⏳ Downloading GPX from {url}")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("Content-Length", 0))

    data = io.BytesIO()

    with rich.progress.Progress() as progress:
        task = progress.add_task("[cyan] Downloading", total=total_size)

        for chunk in response.iter_content(chunk_size=1024):
            data.write(chunk)
            progress.update(task, advance=len(chunk))

    data.seek(0)
    return data

def get_bounds(gpx):
    """
    Return GPX trace bounding box [south, west, north, est]
    """

    min_lat = min(pt.latitude for trk in gpx.tracks for seg in trk.segments for pt in seg.points)
    max_lat = max(pt.latitude for trk in gpx.tracks for seg in trk.segments for pt in seg.points)
    min_lon = min(pt.longitude for trk in gpx.tracks for seg in trk.segments for pt in seg.points)
    max_lon = max(pt.longitude for trk in gpx.tracks for seg in trk.segments for pt in seg.points)
    return min_lat, min_lon, max_lat, max_lon


def query_overpass(bbox, water_types=None, toilet_types=None, repair_types=None, food_types=None):
    """
    Generate an Overpass QL query for potable drinking water POIs, toilets, bicycle repair stations, and food amenities.
    """

    south, west, north, east = bbox
    bbox_str = f"({south},{west},{north},{east})"

    query_parts = []
    
    if water_types:
        for poi_type in water_types:
            tag_filter = WATER_AMENITIES[poi_type]
            # for osm_type in ["node", "way", "relation"]:
            #     query_parts.append(f'{osm_type}{tag_filter}{bbox_str};')
            query_parts.append(f'node{tag_filter}{bbox_str};')
            
    if toilet_types:
        for poi_type in toilet_types:
            tag_filter = TOILET_AMENITIES[poi_type]
            query_parts.append(f'node{tag_filter}{bbox_str};')
            
    if repair_types:
        for poi_type in repair_types:
            tag_filter = REPAIR_AMENITIES[poi_type]
            query_parts.append(f'node{tag_filter}{bbox_str};')
            
    if food_types:
        for poi_type in food_types:
            tag_filter = FOOD_AMENITIES[poi_type]
            query_parts.append(f'node{tag_filter}{bbox_str};')

    query = "[out:json][timeout:25];(" + "".join(query_parts) + ");out center;"
    response = requests.post(OVERPASS_URL, data=query)
    response.raise_for_status()
    return response.json()["elements"]


def add_waypoints_to_gpx(gpx, pois):
    """
    Add POI to GPX trace
    """

    for poi in pois:
        wpt = gpxpy.gpx.GPXWaypoint()
        wpt.latitude = poi["lat"]
        wpt.longitude = poi["lon"]
        
        # Helper function to create POI name (limited to 15 chars)
        def create_poi_name(default_name):
            if "name" in poi["tags"]:
                # Use POI's original name if available, truncated to 15 chars
                return poi["tags"]["name"][:15]
            return default_name[:15]  # Default name truncated to 15 chars
        
        # Determine POI type based on tags
        if "amenity" in poi["tags"]:
            if poi["tags"]["amenity"] == "toilets":
                wpt.name = create_poi_name("Toilets")
                wpt.description = "Toilets"
                wpt.symbol = "restroom"
                wpt.type = "TOILET"
            elif poi["tags"]["amenity"] == "bicycle_repair_station" or \
                 poi["tags"]["amenity"] == "bicycle_rental" or \
                 poi["tags"]["amenity"] == "compressed_air":
                wpt.name = create_poi_name("Repair")
                wpt.description = "Bicycle repair station"
                wpt.symbol = "gear"
                wpt.type = "GEAR"
            elif poi["tags"]["amenity"] in ["cafe", "restaurant", "fast_food"]:
                wpt.name = create_poi_name(poi["tags"]["amenity"].capitalize())
                wpt.description = poi["tags"]["name"] if "name" in poi["tags"] else poi["tags"]["amenity"].capitalize()
                wpt.symbol = "restaurant"
                wpt.type = "FOOD"
            elif poi["tags"]["amenity"] == "drinking_water":
                wpt.name = create_poi_name("Drinking Fountain")
                wpt.description = "Drinking water fountain"
                wpt.symbol = "water-drop"
                wpt.type = "WATER"
            elif poi["tags"]["amenity"] == "water_point" and poi["tags"].get("drinking_water") == "yes":
                wpt.name = create_poi_name("Water Point")
                wpt.description = "Potable water point"
                wpt.symbol = "water-drop"
                wpt.type = "WATER"
            elif poi["tags"]["amenity"] == "fountain" and poi["tags"].get("drinking_water") == "yes":
                wpt.name = create_poi_name("Potable Fountain")
                wpt.description = "Potable decorative fountain"
                wpt.symbol = "water-drop"
                wpt.type = "WATER"
            elif "man_made" in poi["tags"] and poi["tags"]["man_made"] == "water_tap" and poi["tags"].get("drinking_water") == "yes":
                wpt.name = create_poi_name("Water Tap")
                wpt.description = "Potable water tap"
                wpt.symbol = "water-drop"
                wpt.type = "WATER"
            elif "natural" in poi["tags"] and poi["tags"]["natural"] == "spring" and poi["tags"].get("drinking_water") == "yes":
                wpt.name = create_poi_name("Natural Spring")
                wpt.description = "Natural spring with potable water"
                wpt.symbol = "water-drop"
                wpt.type = "WATER"
        elif "shop" in poi["tags"]:
            if poi["tags"]["shop"] == "bicycle":
                wpt.name = create_poi_name("Bike Shop")
                wpt.description = "Bicycle shop with repair service"
                wpt.symbol = "gear"
                wpt.type = "GEAR"
            elif poi["tags"]["shop"] in ["bakery", "supermarket", "convenience", "greengrocer"]:
                wpt.name = create_poi_name(poi["tags"]["shop"].capitalize())
                wpt.description = poi["tags"]["name"] if "name" in poi["tags"] else poi["tags"]["shop"].capitalize()
                wpt.symbol = "shopping"
                wpt.type = "FOOD"
            else:
                # Unknown shop type
                wpt.name = create_poi_name("Unknown Shop")
                wpt.description = f"Shop: {poi['tags']['shop']}"
                wpt.symbol = "water-drop"
                wpt.type = "WATER"
        elif "natural" in poi["tags"] and poi["tags"]["natural"] == "spring":
            # Natural spring without explicit drinking_water tag
            wpt.name = create_poi_name("Spring")
            wpt.description = "Natural spring (drinking quality unknown)"
            wpt.symbol = "water-drop"
            wpt.type = "WATER"
        elif "man_made" in poi["tags"] and poi["tags"]["man_made"] == "water_tap":
            # Water tap without explicit drinking_water tag
            wpt.name = create_poi_name("Water Tap")
            wpt.description = "Water tap (drinking quality unknown)"
            wpt.symbol = "water-drop"
            wpt.type = "WATER"
        else:
            # Default for any other POI detected as water source
            tag_keys = list(poi["tags"].keys())
            tag_summary = ", ".join([f"{k}={poi['tags'][k]}" for k in tag_keys[:2]])
            
            wpt.name = create_poi_name("Water Source")
            wpt.description = f"Water source: {tag_summary}"
            wpt.symbol = "water-drop"
            wpt.type = "WATER"
            
        gpx.waypoints.append(wpt)

    return gpx


def haversine(lat1, lon1, lat2, lon2):
    """
    Return distance in meter between two GPS points
    """

    R = 6371000 # Earth radius in meter
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def filter_pois_near_track(gpx, pois, max_distance_m=100, type_distances=None):
    """
    Keep only POI near trace, with optional distances per POI type
    
    Parameters:
    - gpx: GPX object with the track
    - pois: List of POIs to filter
    - max_distance_m: Default maximum distance in meters
    - type_distances: Dictionary mapping POI types to specific distances
      e.g. {'WATER': 200, 'TOILET': 100, 'GEAR': 300, 'FOOD': 150}
    """
    if type_distances is None:
        type_distances = {}
        
    points = [pt for trk in gpx.tracks for seg in trk.segments for pt in seg.points]
    nearby_pois = []

    for poi in rich.progress.track(pois, description="Filtering POI"):
        lat, lon = poi["lat"], poi["lon"]
        
        # Determine the POI type for distance filtering
        poi_type = "WATER"  # Default type
        if "amenity" in poi["tags"]:
            if poi["tags"]["amenity"] == "toilets":
                poi_type = "TOILET"
            elif poi["tags"]["amenity"] == "bicycle_repair_station" or \
                 poi["tags"]["amenity"] == "bicycle_rental" or \
                 poi["tags"]["amenity"] == "compressed_air":
                poi_type = "GEAR"
            elif poi["tags"]["amenity"] in ["cafe", "restaurant", "fast_food"]:
                poi_type = "FOOD"
        elif "shop" in poi["tags"]:
            if poi["tags"]["shop"] == "bicycle":
                poi_type = "GEAR"
            elif poi["tags"]["shop"] in ["bakery", "supermarket", "convenience", "greengrocer"]:
                poi_type = "FOOD"
                
        # Use type-specific distance if available, otherwise fall back to default
        distance = type_distances.get(poi_type, max_distance_m)
        
        if any(haversine(lat, lon, pt.latitude, pt.longitude) < distance for pt in points):
            nearby_pois.append(poi)

    return nearby_pois


def sanitize_gpx_text(data):
    """
    Fix GPX content by replacing unescaped '&' with '&amp;'
    """

    return re.sub(r'&(?!amp;|quot;|lt;|gt;|apos;)', '&amp;', data)
