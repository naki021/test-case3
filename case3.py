import os
import zipfile
import streamlit as st

# Controleer welke bestanden in /mnt/data/ staan
data_folder = "/mnt/data/"
st.write("📂 Bestanden in /mnt/data/:", os.listdir(data_folder))

# Zoek het ZIP-bestand in /mnt/data/
zip_file = None
for file in os.listdir(data_folder):
    if file.endswith(".zip"):
        zip_file = os.path.join(data_folder, file)
        break

# Als er geen ZIP-bestand is, geef een foutmelding en stop de code
if zip_file is None:
    st.error("❌ Geen ZIP-bestand gevonden in /mnt/data/. Upload het bestand opnieuw.")
    st.stop()

# Pak het ZIP-bestand uit in /tmp/data/
extract_folder = "/tmp/data"
with zipfile.ZipFile(zip_file, 'r') as zip_ref:
    zip_ref.extractall(extract_folder)

# Toon de uitgepakte bestanden
st.write("📂 Bestanden in /tmp/data/:", os.listdir(extract_folder))

# ✅ **Correcte paden voor de submappen**
londen_data_path = "/tmp/data/Londen data"
fiets_data_path = "/tmp/data/Fiets data"
weer_data_path = "/tmp/data/Weer data"


# ✅ **Fietsdata laden**
@st.cache_data
def load_data_fiets():
    fiets_data = []
    bestanden = [
        "270JourneyDataExtract16Jun2021-22Jun2021.csv",
        "271JourneyDataExtract23Jun2021-29Jun2021.csv",
        "269JourneyDataExtract09Jun2021-15Jun2021.csv"
    ]

    for bestand in bestanden:
        pad = os.path.join(fiets_data_path, bestand)

        if os.path.exists(pad):
            fiets_data.append(pd.read_csv(pad))
        else:
            st.error(f"❌ Bestand niet gevonden: {pad}")

    if fiets_data:
        return pd.concat(fiets_data, ignore_index=True)
    else:
        st.error("❌ Geen fietsdata gevonden!")
        return None

# ✅ **Weerdata laden**
@st.cache_data
def load_weather_data():
    pad = os.path.join(weer_data_path, "weather_london.csv")

    if os.path.exists(pad):
        weather_data = pd.read_csv(pad, index_col=0)
        weather_data.index.name = "date"
        weather_data.reset_index(inplace=True)
        return weather_data
    else:
        st.error(f"❌ Bestand niet gevonden: {pad}")
        return None

# ✅ **Kaartfunctie**
if "pagina" in locals() and pagina == "Kaart":
    @st.cache_resource
    def create_m():
        m = folium.Map(location=[51.508586, -0.104444], zoom_start=9)
        plugins.Draw().add_to(m)
        return m

    st.title("London Metro Map")
    m = create_m()
    st_folium(m, width=700, height=500)

# ✅ **Fiets vs Weer**
elif pagina == "Fiets vs Weer":
    st.title("Fietsritten vs Weer in Londen")

    fiets_per_dag_jun = load_data_fiets()
    weather_data = load_weather_data()

    if fiets_per_dag_jun is None or weather_data is None:
        st.error("❌ Data kon niet worden geladen!")
        st.stop()

    # ✅ **Zorg ervoor dat de datumnotaties overeenkomen**
    fiets_per_dag_jun["Date"] = pd.to_datetime(fiets_per_dag_jun["Start Date"]).dt.strftime("%Y-%m-%d")
    weather_data["date"] = pd.to_datetime(weather_data["date"]).dt.strftime("%Y-%m-%d")

    # ✅ **Merge datasets**
    merged_data_jun = fiets_per_dag_jun.merge(weather_data, left_on="Date", right_on="date", how="left")

    if merged_data_jun.empty:
        st.error("❌ Merge tussen fietsritten en weerdata is mislukt! Controleer de datumnotatie.")
    else:
        st.success("✅ Merge succesvol uitgevoerd!")

    # ✅ **Figuur maken**
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(merged_data_jun["Date"], merged_data_jun["Total Rides"], color='b', label="Aantal Fietsritten")
    ax.set_title("Fietsritten vs Weer in Londen")
    ax.set_xlabel("Datum")
    ax.set_ylabel("Aantal Fietsritten")
    ax.legend()
    st.pyplot(fig)
