import os
import json
import calendar
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import folium
import zipfile
import os
from folium import plugins
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression
from branca.colormap import LinearColormap
import os
import json
import pandas as pd
import streamlit as st
import zipfile
import requests

# **ZIP URL**
GITHUB_ZIP_URL = "https://github.com/naki021/test-case3/raw/main/Data.zip"
ZIP_PATH = "./Data.zip"
EXTRACT_PATH = "./extracted_data"

@st.cache_data
def load_train_lines():
    path = os.path.join(BASE_PATH, "Londen data", "stations.json")
    
    if not os.path.exists(path):
        st.error(f"❌ Bestand niet gevonden: {path}")
        return pd.DataFrame()
    
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # **check 'features' **
    if isinstance(data, dict) and "features" in data:
        return pd.json_normalize(data["features"], sep="_")
    elif isinstance(data, list):  
        return pd.json_normalize(data, sep="_")
    else:
        st.error("❌ JSON : 'features' niet gevonden！")
        return pd.DataFrame()


# Functie om het ZIP-bestand uit te pakken
@st.cache_data
def extract_zip(zip_path, extract_to):
    if not os.path.exists(extract_to):
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
    return extract_to

# ZIP-bestand uitpakken
BASE_PATH = extract_zip(ZIP_PATH, EXTRACT_PATH) + "/Data"

@st.cache_data
def load_metro_data():
    """Laadt metro data uit een Excel-bestand (alleen 2021 aanwezig)."""
    data = {}
    for year in range(2021, 2022):  # Alleen 2021-bestand is beschikbaar
        path = os.path.join(BASE_PATH, "Londen data", f"{year}_Entry_Exit.xlsx")
        if os.path.exists(path):
            df = pd.read_excel(path)  # XLSX-bestand lezen
            data[str(year)] = df
    return data

@st.cache_data
def load_weather_data():
    """Laadt weerdata uit het CSV-bestand."""
    path = os.path.join(BASE_PATH, "Weer data", "weather_london.csv")
    if not os.path.exists(path):
        st.error(f"❌ Bestand niet gevonden: {path}")
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str, low_memory=False)
    df["date"] = pd.to_datetime(df["Unnamed: 0"], errors="coerce")
    for col in ["tavg", "tmin", "tmax", "prcp", "wspd", "pres"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df

@st.cache_data
def load_stations():
    """Laadt metrostation data uit een JSON-bestand."""
    path = os.path.join(BASE_PATH, "Londen data", "London stations.json")
    if not os.path.exists(path):
        st.error(f"❌ Bestand niet gevonden: {path}")
        return pd.DataFrame()
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return pd.json_normalize(data["features"], sep="_")

@st.cache_data
def load_train_lines():
    """Laadt treinlijn data uit een JSON-bestand."""
    path = os.path.join(BASE_PATH, "Londen data", "stations.json")
    if not os.path.exists(path):
        st.error(f"❌ Bestand niet gevonden: {path}")
        return pd.DataFrame()
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return pd.json_normalize(data["features"], sep="_")

@st.cache_data
def load_bike_data():
    folder = "./Fiets data"
    geselecteerd = [
        "267JourneyDataExtract26May2021-01Jun2021.csv",
        "268JourneyDataExtract02Jun2021-08Jun2021.csv",
        "294JourneyDataExtract01Dec2021-07Dec2021.csv",
        "295JourneyDataExtract08Dec2021-14Dec2021.csv"
    ]
    all_data = []
    for file in geselecteerd:
        path = os.path.join(folder, file)
        if os.path.exists(path):
            df = pd.read_csv(path)
            all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

#
#

@st.cache_data
def load_bike_data():
    """Laadt fietsdata uit CSV-bestanden"""
    bike_folder = os.path.join(BASE_PATH, "Fiets data")  # 确保路径正确
    all_data = []

    # **check bestand**
    if not os.path.exists(bike_folder):
        st.error(f"❌ Bestand niet gevonden: {bike_folder}")
        return pd.DataFrame()

    for file in os.listdir(bike_folder):
        if file.endswith(".csv"):  #  CSV 文件
            path = os.path.join(bike_folder, file)
            df = pd.read_csv(path, dtype=str, low_memory=False)  # CSV inlezen
            all_data.append(df)

    # **check**
    st.write(f"📊 Gevonden {len(all_data)} fietsdata bestanden")

    if not all_data:
        st.error("❌ Geen fietsdata gevonden!")
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)


# -------------------------------
# PAGINA: KAART EN METRODRUKTE
# -------------------------------
def pagina_kaart():
    stations = load_stations()
    metrodata = load_metro_data()

    st.title("London Metrozone Map")

    @st.cache_resource
    def create_map():
        m = folium.Map(location=[51.508586, -0.104444], zoom_start=9)
        plugins.Draw().add_to(m)
        for _, row in stations.iterrows():
            lat, lon = row['geometry_coordinates'][1], row['geometry_coordinates'][0]
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
        return m

    st_folium(create_map(), width=700, height=500)

    # Legenda
    legenda_kleuren = {
        "Zone 1": "red", "Zone 2": "orange", "Zone 3": "yellow",
        "Zone 4": "GreenYellow", "Zone 5": "green", "Zone 6": "cyan",
        "Buiten Londen": "grey"
    }
    st.markdown("""<br>""", unsafe_allow_html=True)
    legenda_html = " ".join(
        f'<div style="width: 10px; height: 10px; background-color: {kleur}; display: inline-block;"></div> {zone}'
        for zone, kleur in legenda_kleuren.items()
    )
    st.markdown(legenda_html, unsafe_allow_html=True)

    # Dataset selectie
    datasets = metrodata
    dic = {
        'Entry_Week': 'Entry week',
        'Entry_Saturday': 'Entry Saturday',
        'Entry_Sunday': 'Entry Sunday',
        'Exit_Week': 'Exit week',
        'Exit_Saturday': 'Exit Saturday',
        'Exit_Sunday': 'Exit Sunday',
        'AnnualEntryExit_Mill': 'Annual Entry/Exit in millions',
    }

    year = st.slider("Kies een jaar", min_value=2007, max_value=2016, step=1)
    dataset = datasets.get(str(year))

    if dataset is not None:
        column = st.selectbox("Kies een kolom", options=list(dic.keys()))
        dataset[column] = pd.to_numeric(dataset[column], errors='coerce')

        # Kaart met kleuren
        def maak_drukte_kaart():
            p = folium.Map(location=[51.5074, -0.1278], zoom_start=10)
            vmin, vmax = (0, 100) if column == 'AnnualEntryExit_Mill' else (0, 140000)
            colormap = LinearColormap(['green', 'yellow', 'red'], vmin=vmin, vmax=vmax)
            colormap.caption = dic[column]
            p.add_child(colormap)

            for _, row in stations.iterrows():
                naam = row["properties_name"]
                coords = row['geometry_coordinates']
                value = dataset[dataset['Station'] == naam][column].values
                if len(value) == 0 or pd.isna(value[0]):
                    continue
                kleur = colormap(value[0])
                folium.CircleMarker(
                    location=[coords[1], coords[0]],
                    radius=8,
                    color=kleur,
                    fill=True,
                    fill_color=kleur,
                    fill_opacity=0.7,
                    popup=f"{naam}: {value[0]}"
                ).add_to(p)
            return p

        st_folium(maak_drukte_kaart(), width=700, height=500)

        # Tabel top 10
        st.subheader(f"Top 10 drukste stations in {year} op basis van {dic[column]}")
        top10 = dataset[['Station', column]].dropna().sort_values(by=column, ascending=False).head(10)
        top10.reset_index(drop=True, inplace=True)
        top10.index += 1
        st.dataframe(top10)

# -------------------------------
# PAGINA: FIETS VS WEER
# -------------------------------
def pagina_fiets_vs_weer():
    st.title("Fietsritten vs Weer in Londen")
    weer = load_weather_data()
    fiets = load_bike_data()

    weer_opties = {
        "Gemiddelde Temperatuur (°C)": "tavg",
        "Minimale Temperatuur (°C)": "tmin",
        "Maximale Temperatuur (°C)": "tmax",
        "Neerslag (mm)": "prcp",
        "Windkracht (m/s)": "wspd",
        "Luchtdruk (hPa)": "pres"
    }

    keuze = st.selectbox("Kies een weerfactor:", list(weer_opties.keys()))
    kolom = weer_opties[keuze]

    def combineer_fiets_met_weer(df, datumkolom):
        df[datumkolom] = pd.to_datetime(df[datumkolom], errors="coerce")
        df["Date"] = df[datumkolom].dt.date
        per_dag = df.groupby("Date").size().reset_index(name="Total Rides")
        per_dag["Date"] = pd.to_datetime(per_dag["Date"])
        merged = per_dag.merge(weer[["date", kolom]], left_on="Date", right_on="date", how="inner")
        return merged[["Date", "Total Rides", kolom]]

    maanden = [
        ("juni 2021", fiets[fiets["Start Date"].str.contains("05/2021|06/2021", na=False)], "Start Date"),
        ("december 2021", fiets[fiets["Start Date"].str.contains("12/2021", na=False)], "Start Date")
    ]

    fig, axs = plt.subplots(1, 1, figsize=(20, 6))
    for i, (titel, df, datumkolom) in enumerate(maanden):
        data = combineer_fiets_met_weer(df, datumkolom)
        ax = axs[i]
        ax2 = ax.twinx()
        ax.plot(data["Date"], data["Total Rides"], label="Fietsritten", color='blue')
        ax2.plot(data["Date"], data[kolom], label=keuze, color='red', linestyle='dashed')
        ax.set_title(f"{titel.capitalize()}: Fietsritten vs {keuze}")
        ax.set_xlabel("Datum")
        ax.set_ylabel("Aantal Fietsritten", color='blue')
        ax2.set_ylabel(keuze, color='red')

    st.pyplot(fig)

    st.header("🌤️ Gemiddeld weer per maand (2020–2022)")
    label_dict = {
        "tavg": "Gemiddelde temperatuur (°C)",
        "tmin": "Minimale temperatuur (°C)",
        "tmax": "Maximale temperatuur (°C)",
        "prcp": "Neerslag (mm)",
        "wspd": "Windsnelheid (km/u)",
        "pres": "Luchtdruk (hPa)"
    }
    var = st.selectbox("Kies een variabele:", options=list(label_dict.keys()), format_func=lambda x: label_dict[x])
    df = weer.groupby(["year", "month"])[var].mean().reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    for jaar in [2020, 2021, 2022]:
        subset = df[df["year"] == jaar]
        ax.plot(subset["month"], subset[var], marker='o', label=str(jaar))
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels([calendar.month_abbr[m] for m in range(1, 13)])
    ax.set_xlabel("Maand")
    ax.set_ylabel(label_dict[var])
    ax.set_title(f"{label_dict[var]} per maand")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # Voorspelling
    st.subheader("🧠 Voorspelling temperatuur 2023")
    numerieke_kolommen = ["tmin", "tmax", "prcp", "wspd", "pres", "tavg"]
    df_mean = weer.groupby(["year", "month"])[numerieke_kolommen].mean().reset_index()
    model = LinearRegression()
    model.fit(df_mean[["tmin", "tmax", "prcp", "wspd", "pres"]], df_mean["tavg"])

    basis_2023 = df_mean.groupby("month")[["tmin", "tmax", "prcp", "wspd", "pres"]].mean().reset_index()
    voorspelling = model.predict(basis_2023[["tmin", "tmax", "prcp", "wspd", "pres"]])

    fig, ax = plt.subplots(figsize=(10, 5))
    for jaar in [2020, 2021, 2022]:
        subset = df_mean[df_mean["year"] == jaar]
        ax.plot(subset["month"], subset["tavg"], marker='o', label=str(jaar))
    ax.plot(basis_2023["month"], voorspelling, linestyle='dotted', color='deeppink', marker='s', label='Voorspelling 2023')
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels([calendar.month_abbr[m] for m in range(1, 13)])
    ax.set_xlabel("Maand")
    ax.set_ylabel("Gemiddelde temperatuur (°C)")
    ax.set_title("🌡️ Voorspelling temperatuur 2023")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

# -------------------------------
# MAIN
# -------------------------------
pagina = st.sidebar.radio("Selecteer een pagina", ["Kaart", "Fiets vs Weer"])
if pagina == "Kaart":
    pagina_kaart()
elif pagina == "Fiets vs Weer":
    pagina_fiets_vs_weer()
