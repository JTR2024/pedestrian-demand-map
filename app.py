
import streamlit as st
import geopandas as gpd
import folium
import fiona
import branca.colormap as cm
from folium.features import GeoJsonTooltip
from streamlit_folium import st_folium
import tempfile
import os

st.set_page_config(page_title="Pedestrian Demand Map", layout="wide")

st.title("🚶‍♂️ Pedestrian Demand Mapping Tool")
st.code("🔁 This is the latest build – tmp_path is used.")
st.write(
    '''
    1. Upload a GeoPackage (`.gpkg`)  
    2. Pick the layer and numeric fields you want to display  
    3. Explore the interactive Folium map  
    '''
)

uploaded_file = st.file_uploader("Upload your GeoPackage", type=["gpkg"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".gpkg") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        layers = fiona.listlayers(tmp_path)
        layer_choice = st.selectbox("Select a layer:", layers)
        gdf = gpd.read_file(tmp_path, layer=layer_choice)
        st.success(f"Loaded {len(gdf):,} features from **{layer_choice}**")
        st.write("Preview:", gdf.head())

        numeric_fields = gdf.select_dtypes(include=["number"]).columns.tolist()
        if not numeric_fields:
            st.error("No numeric fields found in this layer.")
            st.stop()

        default_selection = ["DemandRank"] if "DemandRank" in numeric_fields else []
        selected_fields = st.multiselect(
            "Select numeric fields to map:", numeric_fields, default=default_selection
        )

        if selected_fields:
            if gdf.crs is None or gdf.crs.to_string() != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)

            center = gdf.geometry.unary_union.centroid
            m = folium.Map(
                location=[center.y, center.x],
                zoom_start=10,
                tiles="CartoDB positron",
            )

            for field in selected_fields:
                colormap = cm.linear.Blues_09.scale(gdf[field].min(), gdf[field].max())
                colormap.caption = field
                colormap.add_to(m)

                tooltip = GeoJsonTooltip(
                    fields=selected_fields,
                    aliases=[f.replace("_", " ").title() for f in selected_fields],
                    localize=True,
                    sticky=False,
                    labels=True,
                )

                folium.GeoJson(
                    gdf,
                    name=field,
                    style_function=lambda feat, field=field: {
                        "fillColor": colormap(feat["properties"][field])
                        if feat["properties"][field] is not None
                        else "#cccccc",
                        "color": "black",
                        "weight": 0.5,
                        "fillOpacity": 0.7,
                    },
                    tooltip=tooltip,
                ).add_to(m)

            folium.LayerControl().add_to(m)

            st.subheader("🗺️ Interactive Map")
            st_folium(m, width=1000, height=600)

    except Exception as e:
        st.error(f"Could not read file: {e}")

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
