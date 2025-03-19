import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import branca.colormap as cm

# ---- Caching de dataset om laadtijd te verkorten ----
@st.cache_data
def load_train_lines():
    with open("./Data/Londen Data/London Train Lines.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.json_normalize(data["features"], sep="_")

@st.cache_data
def load_stations():
    with open("./Data/Londen Data/London stations.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.json_normalize(data["features"], sep="_")

@st.cache_data
def load_weather():
    return pd.read_csv("./Data/Weer data/weather_london.csv")

@st.cache_data
def load_bike_rides():
    return pd.read_csv("./Data/Londen Data/269JourneyDataExtract09Jun2021-15Jun2021.csv")

@st.cache_data
def load_metro_data():
    return pd.read_excel("./Data/Londen Data/2021_Entry_Exit.xlsx")

train_lines = load_train_lines()
stations = load_stations()
weather = load_weather()
bike_rides = load_bike_rides()
metro_data = load_metro_data()

# ---- Sidebar-opties ----
pagina = st.sidebar.radio("Selecteer een visualisatie:", ["Kaart", "Fiets vs Weer", "Metrodrukte vs Fietsritten"])

# ---- Kaart Visualisatie ----
if pagina == "Kaart":
    st.title("Metrokaart van Londen: Zones & Drukte")

    # Dropdown om te kiezen tussen zones en drukte
    kaart_optie = st.selectbox("Kies weergave:", ["Zones", "Drukte"])

    # Kaart aanmaken
    def create_map(kaart_optie):
        m = folium.Map(location=[51.5085, -0.1257], zoom_start=10)

        # Toon metrostationzones
        if kaart_optie == "Zones":
            for _, row in stations.iterrows():
                coords = row["geometry_coordinates"]
                folium.CircleMarker(
                    location=[coords[1], coords[0]],
                    radius=6,
                    color="blue",
                    fill=True,
                    fill_color="blue",
                    fill_opacity=0.7,
                    popup=row["properties_name"]
                ).add_to(m)

        # Toon metrodrukte
        elif kaart_optie == "Drukte":
            colormap = cm.LinearColormap(["green", "yellow", "red"], vmin=0, vmax=100)
            for _, row in metro_data.iterrows():
                station_name = row["Station"]
                waarde = row["AnnualEntryExit_Mill"]
                kleur = colormap(waarde)

                # Coördinaten ophalen
                station_info = stations[stations["properties_name"] == station_name]
                if not station_info.empty:
                    coords = station_info.iloc[0]["geometry_coordinates"]
                    folium.CircleMarker(
                        location=[coords[1], coords[0]],
                        radius=8,
                        color=kleur,
                        fill=True,
                        fill_color=kleur,
                        fill_opacity=0.7,
                        popup=f"{station_name}: {waarde}M"
                    ).add_to(m)

            m.add_child(colormap)

        return m

    map_display = create_map(kaart_optie)
    st_folium(map_display, width=700, height=500)

# ---- Fietsritten vs Weer ----
elif pagina == "Fiets vs Weer":
    st.title("Fietsritten vs Weer in Londen (Juni 2021)")

    # Data voorbereiden
    bike_rides["Start Date"] = pd.to_datetime(bike_rides["Start Date"], format="%d/%m/%Y %H:%M")
    bike_rides["Date"] = bike_rides["Start Date"].dt.date
    fiets_per_dag = bike_rides.groupby("Date").size().reset_index(name="Total Rides")

    weather["date"] = pd.to_datetime(weather["Unnamed: 0"], format="%Y-%m-%d")

    # Weeropties
    weer_opties = {
        "Gemiddelde Temperatuur (°C)": "tavg",
        "Neerslag (mm)": "prcp",
        "Windkracht (m/s)": "wspd"
    }
    
    weer_keuze = st.selectbox("Kies een weerfactor:", list(weer_opties.keys()))

    # Data samenvoegen
    merged_data = fiets_per_dag.merge(weather[["date", weer_opties[weer_keuze]]], left_on="Date", right_on="date", how="inner")

    # Lijndiagram
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(merged_data["Date"], merged_data["Total Rides"], color='b', label="Aantal Fietsritten")
    ax1.set_ylabel("Aantal Fietsritten", color="b")
    ax1.tick_params(axis='y', labelcolor="b")

    ax2 = ax1.twinx()
    ax2.plot(merged_data["Date"], merged_data[weer_opties[weer_keuze]], color='r', linestyle="dashed", label=weer_keuze)
    ax2.set_ylabel(weer_keuze, color="r")
    ax2.tick_params(axis='y', labelcolor="r")

    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    plt.title(f"Aantal fietsritten vs {weer_keuze} in juni 2021")
    plt.xticks(rotation=45)
    
    st.pyplot(fig)

# ---- Metrodrukte vs Fietsritten ----
elif pagina == "Metrodrukte vs Fietsritten":
    st.title("Metrodrukte vs Fietsritten in Londen (2021)")

    # Gemiddelde metrodrukte per maand
    metro_data["Month"] = pd.to_datetime(metro_data["Date"]).dt.month
    metro_gemiddeld = metro_data.groupby("Month")["AnnualEntryExit_Mill"].mean()

    # Fietsritten per maand
    bike_rides["Month"] = pd.to_datetime(bike_rides["Start Date"]).dt.month
    fiets_gemiddeld = bike_rides.groupby("Month").size()

    # Lijndiagram
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(fiets_gemiddeld.index, fiets_gemiddeld.values, color='b', label="Aantal Fietsritten")
    ax1.set_xlabel("Maand")
    ax1.set_ylabel("Aantal Fietsritten", color="b")
    ax1.tick_params(axis='y', labelcolor="b")

    ax2 = ax1.twinx()
    ax2.plot(metro_gemiddeld.index, metro_gemiddeld.values, color='r', linestyle="dashed", label="Metrodrukte (miljoenen)")
    ax2.set_ylabel("Metrodrukte (miljoenen)", color="r")
    ax2.tick_params(axis='y', labelcolor="r")

    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    plt.title("Metrodrukte vs Fietsritten in 2021")
    plt.xticks(range(1, 13))

    st.pyplot(fig)
