import streamlit as st
import geopandas as gpd
import folium
import fiona
import branca.colormap as cm
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium
import tempfile

st.set_page_config(page_title="Pedestrian Demand Map", layout="wide")

st.title("🚶‍♂️ Pedestrian Demand Mapping Tool")
st.write("Upload a GeoPackage, select a layer and fields, and generate an interactive map.")

# File upload
uploaded_file = st.file_uploader("Upload your GeoPackage (.gpkg)", type=["gpkg"])

if uploaded_file:
    # Save uploaded file to a temporary file on disk
    with tempfile.NamedTemporaryFile(delete=False, suffix=".gpkg") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        # List layers
        layers = fiona.listlayers(tmp_path)
        layer_choice = st.selectbox("Select a layer:", layers)

        # Load GeoDataFrame
        gdf = gpd.read_file(tmp_path, layer=layer_choice)

        # Show preview
        st.write("Data Preview:", gdf.head())

        # Select numeric fields
        numeric_fields = gdf.select_dtypes(include=["number"]).columns.tolist()
        selected_fields = st.multiselect("Select fields to visualize:", numeric_fields, default=["DemandRank"] if "DemandRank" in numeric_fields else [])

        if selected_fields:
            # Convert CRS to WGS84 for Folium
            if gdf.crs is None or gdf.crs.to_string() != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)

            # Create Folium map
            center = gdf.geometry.unary_union.centroid
            m = folium.Map(location=[center.y, center.x], zoom_start=10, tiles="CartoDB positron")

            for field in selected_fields:
                colormap = cm.linear.Blues_09.scale(gdf[field].min(), gdf[field].max())
                colormap.caption = field
                colormap.add_to(m)

                tooltip = GeoJsonTooltip(
                    fields=selected_fields,
                    aliases=[f.replace("_", " ").title() for f in selected_fields],
                    localize=True,
                    labels=True,
                    sticky=False
                )

                folium.GeoJson(
                    gdf,
                    name=field,
                    style_function=lambda feature, field=field: {
                        "fillColor": colormap(feature["properties"][field]) if feature["properties"][field] is not None else "#ccc",
                        "color": "black",
                        "weight": 0.5,
                        "fillOpacity": 0.7,
                    },
                    tooltip=tooltip
                ).add_to(m)

            folium.LayerControl().add_to(m)

            # Display map
            st.subheader("🗺️ Interactive Map")
            st_folium(m, width=1000, height=600)

    except Exception as e:
        st.error(f"Error reading file: {e}")
