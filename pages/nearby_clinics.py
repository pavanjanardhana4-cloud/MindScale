"""
MindScale AI - Nearby Clinics Page

Find nearby hospitals/clinics using OpenStreetMap (Nominatim + Overpass).
"""

import math
from typing import List, Dict, Optional, Tuple

import requests
import streamlit as st


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    """Reverse‑geocode coordinates to a human‑readable address using Nominatim."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat,
                "lon": lon,
                "format": "json",
                "zoom": 18,
                "addressdetails": 1,
            },
            headers={"User-Agent": "MindScaleAI/1.0 (Streamlit)"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("display_name")
    except Exception:
        return None


def geocode_location(query: str) -> Optional[Tuple[float, float, str]]:
    """
    Geocode a free‑text location string to (lat, lon, display_name) using Nominatim.
    """
    if not query.strip():
        return None

    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": "MindScaleAI/1.0 (Streamlit)"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        item = data[0]
        return float(item["lat"]), float(item["lon"]), item.get("display_name", query)
    except Exception:
        return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great‑circle distance between two points in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(
        dlambda / 2
    ) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def fetch_nearby_hospitals(
    lat: float, lon: float, radius_km: float = 5.0
) -> List[Dict[str, object]]:
    """
    Query Overpass API for hospitals within radius_km of (lat, lon).

    Returns a list of dicts with name, lat, lon, and distance_km.
    """
    radius_m = int(radius_km * 1000)
    # Overpass QL: hospitals around a point
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:{radius_m},{lat},{lon});
      way["amenity"="hospital"](around:{radius_m},{lat},{lon});
      relation["amenity"="hospital"](around:{radius_m},{lat},{lon});
    );
    out center;
    """
    try:
        resp = requests.post(
            OVERPASS_URL,
            data=query,
            headers={"User-Agent": "MindScaleAI/1.0 (Streamlit)"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    hospitals: List[Dict[str, object]] = []
    for el in data.get("elements", []):
        tags = el.get("tags", {}) or {}
        name = tags.get("name")
        # Determine coordinates
        if el.get("type") == "node":
            h_lat, h_lon = el.get("lat"), el.get("lon")
        else:
            center = el.get("center") or {}
            h_lat, h_lon = center.get("lat"), center.get("lon")
        if h_lat is None or h_lon is None:
            continue
        distance_km = haversine_km(lat, lon, h_lat, h_lon)
        address_parts = [
            tags.get("addr:street"),
            tags.get("addr:housenumber"),
            tags.get("addr:city"),
        ]
        address = ", ".join([p for p in address_parts if p])
        hospitals.append(
            {
                "name": name or "Unnamed hospital",
                "distance_km": round(distance_km, 2),
                "lat": h_lat,
                "lon": h_lon,
                "address": address,
            }
        )

    # Try to fill missing addresses with a light reverse‑geocode pass (limit to 15 to be polite)
    missing_count = 0
    for h in hospitals:
        if not h["address"] and missing_count < 15:
            addr = reverse_geocode(h["lat"], h["lon"])
            if addr:
                h["address"] = addr
            missing_count += 1

    hospitals.sort(key=lambda x: x["distance_km"])
    return hospitals


def render():
    """Render the nearby clinics page."""
    st.markdown("# 🏥 Nearby Clinics")
    st.markdown(
        "Find hospitals and clinics near you using OpenStreetMap data. "
        "Enter a location to see nearby options."
    )
    st.markdown("---")

    with st.container():
        col_left, col_right = st.columns([2, 1])
        with col_left:
            location_query = st.text_input(
                "Enter your city, address, or landmark",
                placeholder="e.g., MG Road, Bengaluru or 560001",
            )
        with col_right:
            radius_km = st.slider(
                "Search radius (km)", min_value=1.0, max_value=20.0, value=5.0, step=1.0
            )

    search_clicked = st.button("Find nearby hospitals")

    if not search_clicked:
        st.info("Enter a location and click **Find nearby hospitals** to begin.")
        return

    with st.spinner("Locating and searching nearby hospitals..."):
        geocoded = geocode_location(location_query)
        if not geocoded:
            st.error(
                "Could not find that location. Please try a different city, address, or postal code."
            )
            return
        lat, lon, display_name = geocoded
        hospitals = fetch_nearby_hospitals(lat, lon, radius_km=radius_km)

    st.markdown("---")
    st.markdown(f"### Results near: `{display_name}`")

    if not hospitals:
        st.warning(
            f"No hospitals found within {radius_km:.0f} km. "
            "Try increasing the radius or using a more general location."
        )
        return

    # Summary chips
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Hospitals found", len(hospitals))
    with c2:
        st.metric("Closest distance", f"{hospitals[0]['distance_km']} km")

    # Clean table
    st.markdown("#### Nearby hospitals")
    for idx, h in enumerate(hospitals, start=1):
        with st.container():
            st.markdown(
                f"**{idx}. {h['name']}**  \n"
                f"Distance: `{h['distance_km']} km`  \n"
                f"Address: `{h['address'] or 'Not available'}`"
            )
            st.markdown("---")


