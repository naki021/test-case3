import pandas as pd
import json
import streamlit as st
import folium
from streamlit_folium import st_folium
from folium import plugins
import matplotlib.pyplot as plt
import branca.colormap as cm
import zipfile
import os

# Definieer paden
zip_path = "Data.zip"
extract_folder = "/tmp/data/Data"

# Pak het ZIP-bestand uit als het nog niet is uitgepakt
if not os.path.exists(extract_folder):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)

# Controleer welke bestanden en mappen nu in extract_folder staan
st.write("📂 Bestanden in /tmp/data:", os.listdir(extract_folder))

# Controleer of de submappen correct zijn
londen_data_path = os.path.join(extract_folder, "Londen data")
fiets_data_path = os.path.join(extract_folder, "Fiets data")

if os.path.exists(londen_data_path):
    st.write("📂 Bestanden in Londen data:", os.listdir(londen_data_path))
else:
    st.error("❌ Map 'Londen data' niet gevonden!")

if os.path.exists(fiets_data_path):
    st.write("📂 Bestanden in Fiets data:", os.listdir(fiets_data_path))
else:
    st.error("❌ Map 'Fiets data' niet gevonden!")

## begin

@st.cache_data
def load_data_fiets():
    fiets_data = []
    fiets_pad = "/tmp/data/Fiets data"

    bestanden = [
        "270JourneyDataExtract16Jun2021-22Jun2021.csv",
        "271JourneyDataExtract23Jun2021-29Jun2021.csv",
        "269JourneyDataExtract09Jun2021-15Jun2021.csv"
    ]

    for bestand in bestanden:
        pad = os.path.join(fiets_pad, bestand)

        if os.path.exists(pad):
            fiets_data.append(pd.read_csv(pad))
        else:
            st.error(f"❌ Bestand niet gevonden: {pad}")

    # Combineer alle bestanden in één DataFrame
    if fiets_data:
        return pd.concat(fiets_data, ignore_index=True)
    else:
        st.error("❌ Geen fietsdata gevonden!")
        return None
##einde een

@st.cache_data
def load_stations():
    pad = "/tmp/data/Data/Londen data/London stations.json"
    if os.path.exists(pad):
        with open(pad, "r", encoding="utf-8") as file:
            data = json.load(file)
        return pd.json_normalize(data["features"], sep="_")
    else:
        st.error(f"❌ Bestand niet gevonden: {pad}")
        return None

##einde 2

if "pagina" in locals() and pagina == "Kaart":
    @st.cache_resource
    def create_m():
        m = folium.Map(location=[51.508586, -0.104444], zoom_start=9)
        plugins.Draw().add_to(m)

        station1 = load_stations()

        for _, row in station1.iterrows():
            coords = row['geometry_coordinates']
            lat, lon = coords[1], coords[0]
            color = row.get("properties_marker-color", "gray")  # Haal de kleur op uit de kolom 'properties_marker-color'

            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=row["properties_name"]
            ).add_to(m)

        return m  # Zorg dat return buiten de for-loop staat

    st.title("London Metro Map")

    m = create_m()
    st_folium(m, width=700, height=500)
    
    dic = {
    'Entry_Week': 'Entry week',
    'Entry_Saturday': 'Entry Saturday',
    'Entry_Sunday': 'Entry Sunday',
    'Exit_Week': 'Exit week',
    'Exit_Saturday': 'Exit Saturday',
    'Exit_Sunday': 'Exit Sunday',
    'AnnualEntryExit_Mill': 'Annual Entry/Exit in millions',
}


# Haal de geselecteerde dataset op
    dataset = datasets[str(year)]

# Hardcoded kolom die je wilt gebruiken voor de visualisatie
    column = st.selectbox("Kies een kolom", options=list(dic.keys()))
    column1 = 'Station'  # Kolom die stationnamen bevat

# Zorg ervoor dat de data numeriek zijn
    dataset[column] = pd.to_numeric(dataset[column], errors='coerce')

# Creëer de kaart
    def create_p():
        p = folium.Map(location=[51.5074, -0.1278], zoom_start=10)  # Londen coördinaten

    # Bepaal de min/max van de geselecteerde kolom
        vmin = 0
        vmax = 100

    # Creëer een lineaire colormap (groen -> geel -> rood)
        colormap = cm.LinearColormap(colors=['green', 'yellow', 'red'], vmin=vmin, vmax=vmax)
        colormap.caption = f'{column} (in miljoenen)'  # Voeg de gekozen kolomnaam toe aan de colormap
        p.add_child(colormap)

    # Itereer over de stations en pas de juiste kleuren toe
        for idx, row in station1.iterrows():
            station_name = row["properties_name"]  # Stationnaam uit station1
        # Zoek de waarde voor de gekozen kolom voor het station
            value = dataset[dataset[column1] == station_name][column].values

            if len(value) > 0:
                value = value[0]  # Haal de eerste waarde uit de lijst (aangenomen dat het unieke station is)
            else:
                value = None  # Geen waarde gevonden

            if pd.isna(value):
            # Geen data gevonden? Gebruik een standaard kleur
                continue
            else:
            # Bepaal de kleur op basis van de colormap
                color = colormap(value)

        # Haal de coördinaten op (ervan uitgaande dat dit [lon, lat] is)
            coords = row['geometry_coordinates']
            lon, lat = coords[0], coords[1]

        # Voeg de marker toe aan de kaart
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=f"{station_name}: {value}"
            ).add_to(p)

        return p

# Titel van de pagina
    st.title(f"London Metro Map met {column} Data - {year}")

# Genereer de kaart
    p = create_p()

# Toon de kaart in Streamlit
    st_folium(p, width=700, height=500)

# Sidebar met tabbladen
pagina = st.sidebar.radio("Selecteer een pagina", ['Kaart', 'Fiets vs Weer'])

if pagina == "Kaart":
    @st.cache_resource
    def create_m():
        m = folium.Map(location=[51.508586, -0.104444], zoom_start=9)
        plugins.Draw().add_to(m)

        station1 = load_stations()

        for _, row in station1.iterrows():
            coords = row['geometry_coordinates']
            lat, lon = coords[1], coords[0]
            color = row.get("properties_marker-color", "gray")

            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=row["properties_name"]
            ).add_to(m)

        return m  # Zorg dat return buiten de for-loop staat

    st.title("London Metro Map")
    m = create_m()
    st_folium(m, width=700, height=500)

elif pagina == "Fiets vs Weer":  # ✅ Nu werkt elif correct!
    st.title("Fietsritten vs Weer in Londen")
    
##nieuw begin
    st.write("📂 Eerste paar rijen van fiets_per_dag_jun1:", fiets_per_dag_jun1.head())
st.write("📂 Kolommen in fiets_per_dag_jun1:", fiets_per_dag_jun1.columns)

st.write("📂 Eerste paar rijen van weather_data:", weather_data.head())
st.write("📂 Kolommen in weather_data:", weather_data.columns)

st.write("📂 Eerste paar rijen van merged_data_jun1:", merged_data_jun1.head())
st.write("📂 Aantal rijen in merged_data_jun1:", len(merged_data_jun1))

# Zorg ervoor dat de datumnotaties overeenkomen
fiets_per_dag_jun1["Date"] = pd.to_datetime(fiets_per_dag_jun1["Date"]).dt.strftime("%Y-%m-%d")
weather_data["date"] = pd.to_datetime(weather_data["date"]).dt.strftime("%Y-%m-%d")

# Merge de datasets opnieuw
merged_data_jun1 = fiets_per_dag_jun1.merge(
    weather_data, left_on="Date", right_on="date", how="left"
)

# Controleer of de merge werkt
if merged_data_jun1.empty:
    st.error("❌ Merge tussen fietsritten en weerdata is mislukt! Controleer de datumnotatie.")
else:
    st.success("✅ Merge succesvol uitgevoerd!")
    
 # Laad de fietsdata correct in
jun2021 = load_data_fiets()

# Converteer de datumkolom naar een datetime-formaat
jun2021["Start Date"] = pd.to_datetime(jun2021["Start Date"], format="%d/%m/%Y %H:%M")
jun2021["Date"] = jun2021["Start Date"].dt.date

# Laad de weerdata correct in
weather_data = pd.read_csv("/tmp/data/Weer data/weather_london.csv")

# Hernoem de kolommen en converteer de datum
weather_data.rename(columns={"Unnamed: 0": "date"}, inplace=True)
weather_data["date"] = pd.to_datetime(weather_data["date"], format="%Y-%m-%d")

# Beschikbare weeropties
weer_opties = {
    "Gemiddelde Temperatuur (°C)": "tavg",
    "Minimale Temperatuur (°C)": "tmin",
    "Maximale Temperatuur (°C)": "tmax",
    "Neerslag (mm)": "prcp",
    "Windkracht (m/s)": "wspd",
    "Luchtdruk (hPa)": "pres"
}

# Vraag de gebruiker om een weerfactor te kiezen
weer_keuze = st.selectbox("Kies een weerfactor:", list(weer_opties.keys()))

# Data combineren op datum
fiets_per_dag_jun1["Date"] = pd.to_datetime(fiets_per_dag_jun1["Date"])
elif pagina == "Fiets vs Weer":
    st.title("Fietsritten vs Weer in Londen")

    # Data combineren op datum
    fiets_per_dag_jun1["Date"] = pd.to_datetime(fiets_per_dag_jun1["Date"])

    toegevoegde_data_jun1 = weather_data[["date", weer_opties[weer_keuze]]]
    merged_data_jun1 = fiets_per_dag_jun1.merge(
        toegevoegde_data_jun1, left_on="Date", right_on="date", how="inner"
    )
    merged_data_jun1 = merged_data_jun1[["Date", "Total Rides", weer_opties[weer_keuze]]]

    # Data combineren op datum voor tweede dataset (juni 2022)
    fiets_per_dag_jun2["Date"] = pd.to_datetime(fiets_per_dag_jun2["Date"])
    toegevoegde_data_jun2 = weather_data[["date", weer_opties[weer_keuze]]]
    merged_data_jun2 = fiets_per_dag_jun2.merge(
        toegevoegde_data_jun2, left_on="Date", right_on="date", how="inner"
    )
    merged_data_jun2 = merged_data_jun2[["Date", "Total Rides", weer_opties[weer_keuze]]]

##einde

# figuur met 6 grafieken over fietsritten vs weer
fig, ax = plt.subplots(2, 2, figsize=(22, 15), sharex=False)

# grafiek [0,0]
ax1 = ax[0,0]
ax1.plot(merged_data_jun1["Date"], merged_data_jun1["Total Rides"], color='b', label="Aantal Fietsritten")
ax1.set_title(f"Aantal fietsritten en {weer_keuze} in juni 2021")
ax1.set_xlim([pd.to_datetime('2021-06-01'), pd.to_datetime('2021-06-30')])
ax1.set_xlabel("Datum")
ax1.set_ylabel("Aantal Fietsritten", color='b')
ax1.tick_params(axis='y', labelcolor='b')

ax2 = ax1.twinx()
ax2.plot(merged_data_jun1["Date"], merged_data_jun1[weer_opties[weer_keuze]], color='r', linestyle="dashed", label=weer_keuze)
ax2.set_ylabel(weer_keuze, color='r')
ax2.tick_params(axis='y', labelcolor='r')

ax1.legend(loc="upper left")
ax2.legend(loc="upper right")

# grafiek [1,0]
ax5 = ax[1,0]
ax5.plot(merged_data_jun2["Date"], merged_data_jun2["Total Rides"], color='b', label="Aantal Fietsritten")
ax5.set_title(f"Aantal fietsritten en {weer_keuze} in juni 2022")
ax5.set_xlim([pd.to_datetime('2022-06-01'), pd.to_datetime('2022-06-30')])
ax5.set_xlabel("Datum")
ax5.set_ylabel("Aantal Fietsritten", color='b')
ax5.tick_params(axis='y', labelcolor='b')

ax6 = ax5.twinx()
ax6.plot(merged_data_jun2["Date"], merged_data_jun2[weer_opties[weer_keuze]], color='r', linestyle="dashed", label=weer_keuze)
ax6.set_ylabel(weer_keuze, color='r')
ax6.tick_params(axis='y', labelcolor='r')

ax5.legend(loc="upper left")
ax6.legend(loc="upper right")

fig.suptitle(f"Aantal fietsritten vs {weer_keuze} in Londen")
plt.tight_layout()
st.pyplot(fig)
