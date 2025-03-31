import streamlit as st
import pandas as pd
import numpy as np
import io
import base64
import re
from pathlib import Path
import os

# Set page configuration
st.set_page_config(
    page_title="Création d'un audit sémantique",
    page_icon="✍️",
    layout="wide"
)

# Apply custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    h1 {
        margin-bottom: 2rem;
    }
    .stExpander {
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    
    /* Custom styling for sidebar */
    .css-1d391kg {
        background-image: url('data:image/png;base64,iVBORw...'); /* Add your logo base64 here */
        background-repeat: no-repeat;
        padding-top: 80px;
        background-position: 20px 20px;
    }
</style>
""", unsafe_allow_html=True)

# Add sidebar
st.sidebar.title("Navigation")
st.sidebar.header("Compte Google")
selected_account = st.sidebar.selectbox("Compte Google", ["Sélectionner un compte", "Mon Compte Google"])
if selected_account == "Sélectionner un compte":
    st.sidebar.markdown("[Connecter un compte Google](#)")

# Main title
st.title("Création d'un audit sémantique")

# Information sections
with st.expander("Pourquoi utiliser ce script ?", expanded=True):
    st.markdown("""
    Ce script permet d'identifier les mots-clés à cibler pour sur un site grâce à une analyse concurrentielle, 
    en comparant ses mots-clés positionnés par rapport à ceux de ses concurrents.
    
    🠚 [Exemple de fichier généré par ce script](#)
    """)

with st.expander("Comment utiliser ce script ?", expanded=True):
    st.markdown("""
    1. **Exporter les mots-clés positionnés de plusieurs sites** depuis Ahrefs, SEMrush, ou une autre source de données.
    
    2. **Importer les fichiers** d'une même source, et d'un même format, dans la zone d'import de fichiers ci-dessous.
    
    3. **Configurer le mapping des colonnes** en sélectionnant une des préconfiguration si possible, sinon, en sélectionnant "Custom", et renseignant manuellement le nom des colonnes nécessaires à l'analyse.
    
    4. **Configurer la façon de filtrer les données dans l'analyse concurrentielle** en sélectionnant une des préconfiguration si possible, sinon, en sélectionnant "Custom", et renseignant manuellement les valeurs.
    
    5. Cliquer sur **Lancer l'analyse**.
    """)

# File uploader
uploaded_files = st.file_uploader("Importer les fichiers de données :", 
                                  type=["csv", "xlsx"], 
                                  accept_multiple_files=True)

# Configuration des colonnes
st.header("Configuration des colonnes")

column_config_type = st.selectbox(
    "Sélectionner un **type de configuration** :",
    ["Custom", "SEMrush", "Ahrefs", "Google Search Console"]
)

# Définir les configurations prédéfinies
config_presets = {
    "SEMrush": {
        "keyword": "Keyword",
        "volume": "Volume",
        "position": "Position",
        "url": "URL"
    },
    "Ahrefs": {
        "keyword": "Keyword",
        "volume": "Volume",
        "position": "Position",
        "url": "URL"
    },
    "Google Search Console": {
        "keyword": "Query",
        "volume": "",
        "position": "Position",
        "url": "Page"
    },
    "Custom": {
        "keyword": "",
        "volume": "",
        "position": "",
        "url": ""
    }
}

# Afficher les champs de saisie en fonction de la configuration sélectionnée
selected_config = config_presets[column_config_type]

if column_config_type == "Custom":
    keyword_col = st.text_input("Colonne **Mot-clé** :")
    volume_col = st.text_input("Colonne **Volume de recherche** :")
    position_col = st.text_input("Colonne **Position** :")
    url_col = st.text_input("Colonne **Page** :")
else:
    keyword_col = selected_config["keyword"]
    volume_col = selected_config["volume"]
    position_col = selected_config["position"]
    url_col = selected_config["url"]
    
    st.text_input("Colonne **Mot-clé** :", value=keyword_col)
    st.text_input("Colonne **Volume de recherche** :", value=volume_col)
    st.text_input("Colonne **Position** :", value=position_col)
    st.text_input("Colonne **Page** :", value=url_col)

# Configuration des filtres
st.header("Configuration des filtres")

filter_options = [
    "Custom",
    "Toutes les données",
    "Au moins 1 site positionné dans le top 10",
    "Au moins 1 site positionné dans le top 20",
    "Au moins 1 site positionné dans le top 30",
    "Au moins 2 sites positionnés, dont 1 top 10",
    "Au moins 2 sites positionnés, dont 1 top 20",
    "Au moins 2 sites positionnés, dont 1 top 30",
]

filter_config_type = st.selectbox(
    "Sélectionner un **type de configuration** :",
    filter_options
)

# Définir les configurations de filtres prédéfinies
filter_presets = {
    "Toutes les données": {
        "min_sites": 0,
        "min_sites_top_positions": 0,
        "top_positions": 0,
        "description": "Affiche toutes les données sans filtrage"
    },
    "Au moins 1 site positionné dans le top 10": {
        "min_sites": 1,
        "min_sites_top_positions": 1,
        "top_positions": 10,
        "description": "Filtre les mots-clés pour lesquels au moins un site est positionné dans le top 10"
    },
    "Au moins 1 site positionné dans le top 20": {
        "min_sites": 1,
        "min_sites_top_positions": 1,
        "top_positions": 20,
        "description": "Filtre les mots-clés pour lesquels au moins un site est positionné dans le top 20"
    },
    "Au moins 1 site positionné dans le top 30": {
        "min_sites": 1,
        "min_sites_top_positions": 1,
        "top_positions": 30,
        "description": "Filtre les mots-clés pour lesquels au moins un site est positionné dans le top 30"
    },
    "Au moins 2 sites positionnés, dont 1 top 10": {
        "min_sites": 2,
        "min_sites_top_positions": 1,
        "top_positions": 10,
        "description": "Filtre les mots-clés pour lesquels au moins 2 sites sont positionnés, dont au moins 1 dans le top 10"
    },
    "Au moins 2 sites positionnés, dont 1 top 20": {
        "min_sites": 2,
        "min_sites_top_positions": 1,
        "top_positions": 20,
        "description": "Filtre les mots-clés pour lesquels au moins 2 sites sont positionnés, dont au moins 1 dans le top 20"
    },
    "Au moins 2 sites positionnés, dont 1 top 30": {
        "min_sites": 2,
        "min_sites_top_positions": 1,
        "top_positions": 30,
        "description": "Filtre les mots-clés pour lesquels au moins 2 sites sont positionnés, dont au moins 1 dans le top 30"
    },
    "Custom": {
        "min_sites": 0,
        "min_sites_top_positions": 0,
        "top_positions": 0,
        "description": "Configuration personnalisée"
    }
}

# Afficher les champs de saisie en fonction de la configuration sélectionnée
if filter_config_type in filter_presets:
    selected_filter = filter_presets[filter_config_type]
    
    if filter_config_type == "Custom":
        st.info("Configuration personnalisée des filtres")
        min_sites = st.number_input("Nombre minimum de sites se positionnant sur le mot-clé :", min_value=0, value=0)
        top_positions = st.number_input("Position maximum (top X) :", min_value=0, value=0)
        min_sites_top = st.number_input("Nombre minimum de sites se positionnant dans les X premières positions :", min_value=0, value=0)
    else:
        st.info(selected_filter["description"])
        
        # Afficher les valeurs mais de manière non interactive
        min_sites = selected_filter["min_sites"]
        top_positions = selected_filter["top_positions"]
        min_sites_top = selected_filter["min_sites_top_positions"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Nombre minimum de sites", min_sites)
            st.metric("Minimum dans le top", min_sites_top)
        with col2:
            st.metric("Position top X", top_positions)
            
        # Ajouter des champs cachés pour stocker les valeurs
        st.session_state.min_sites = min_sites
        st.session_state.top_positions = top_positions
        st.session_state.min_sites_top = min_sites_top

# Options
st.header("Options")
create_specific_tabs = st.checkbox("Créer les onglets d'analyse spécifiques à chaque fichier", value=True)

# Warning
st.warning("Veuillez sélectionner votre compte nominatif avant de lancer l'analyse (et non le compte GSC).")

# Function to process the data
def process_data(files, config, filters, create_tabs):
    if not files:
        return None
    
    # Extract configuration
    keyword_column = config["keyword"]
    volume_column = config["volume"]
    position_column = config["position"]
    url_column = config["url"]
    
    # Extract filters
    min_sites_filter = filters["min_sites"]
    top_x_positions = filters["top_positions"]
    min_sites_top_x = filters["min_sites_top_positions"]
    
    # Initialize dataframes dictionary
    dfs = {}
    all_data = []
    
    # Read each file
    for file in files:
        file_extension = file.name.split('.')[-1].lower()
        file_name = file.name.split('.')[0]
        
        try:
            if file_extension == 'csv':
                df = pd.read_csv(file)
            elif file_extension == 'xlsx':
                df = pd.read_excel(file)
            else:
                st.error(f"Format de fichier non pris en charge: {file.name}")
                continue
                
            # Check if required columns exist
            required_columns = [keyword_column, position_column, url_column]
            if volume_column:  # Only check if provided
                required_columns.append(volume_column)
                
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.error(f"Colonnes manquantes dans {file.name}: {', '.join(missing_columns)}")
                continue
            
            # Add source column
            df['Source'] = file_name
            
            # Clean and normalize data
            df[keyword_column] = df[keyword_column].astype(str).str.lower().str.strip()
            df[keyword_column] = df[keyword_column].apply(lambda x: re.sub(r'\s+', ' ', x))
            
            # Ensure position column is numeric
            df[position_column] = pd.to_numeric(df[position_column], errors='coerce')
            
            # Clean URL if present
            if url_column in df.columns:
                df[url_column] = df[url_column].astype(str).str.lower()
                df[url_column] = df[url_column].apply(lambda x: re.sub(r'^https?://', '', x))
                df[url_column] = df[url_column].apply(lambda x: re.sub(r'/

# Process button
if st.button("Lancer l'analyse", disabled=(selected_account == "Sélectionner un compte")):
    if not uploaded_files:
        st.error("Veuillez importer au moins un fichier pour l'analyse.")
    else:
        # Prepare configuration
        config = {
            "keyword": keyword_col,
            "volume": volume_col,
            "position": position_col,
            "url": url_col
        }
        
        # Get filter values either from session state (for preset filters) or from input fields (for custom)
        if filter_config_type != "Custom" and filter_config_type in filter_presets:
            min_sites_val = filter_presets[filter_config_type]["min_sites"]
            top_positions_val = filter_presets[filter_config_type]["top_positions"]
            min_sites_top_val = filter_presets[filter_config_type]["min_sites_top_positions"]
        else:
            min_sites_val = min_sites
            top_positions_val = top_positions
            min_sites_top_val = min_sites_top
        
        filters = {
            "min_sites": min_sites_val,
            "top_positions": top_positions_val,
            "min_sites_top_positions": min_sites_top_val
        }
        
        # Show processing message
        with st.spinner("Traitement des données en cours..."):
            # Process data
            excel_data = process_data(uploaded_files, config, filters, create_specific_tabs)
            
            if excel_data:
                # Create download link
                b64 = base64.b64encode(excel_data.read()).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="analyse_semantique.xlsx" class="download-button">Télécharger le fichier Excel d\'analyse</a>'
                
                st.markdown("""
                <style>
                .download-button {
                    display: inline-block;
                    padding: 0.5em 1em;
                    color: white;
                    background-color: #4CAF50;
                    text-decoration: none;
                    border-radius: 4px;
                    font-weight: bold;
                    margin: 1em 0;
                }
                .download-button:hover {
                    background-color: #45a049;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(href, unsafe_allow_html=True)
                st.success("Analyse terminée avec succès ! Cliquez sur le bouton ci-dessus pour télécharger le fichier d'analyse.")
, '', x))
            
            # Add to list of dataframes
            dfs[file_name] = df
            all_data.append(df)
            
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier {file.name}: {str(e)}")
    
    if not dfs:
        return None
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Add formats for Excel
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4B88B6',
            'font_color': 'white',
            'border': 1
        })
        
        position_format = workbook.add_format({
            'num_format': '0.0',
            'border': 1
        })
        
        volume_format = workbook.add_format({
            '

# Process button
if st.button("Lancer l'analyse", disabled=(selected_account == "Sélectionner un compte")):
    if not uploaded_files:
        st.error("Veuillez importer au moins un fichier pour l'analyse.")
    else:
        # Prepare configuration
        config = {
            "keyword": keyword_col,
            "volume": volume_col,
            "position": position_col,
            "url": url_col
        }
        
        # Get filter values either from session state (for preset filters) or from input fields (for custom)
        if filter_config_type != "Custom" and filter_config_type in filter_presets:
            min_sites_val = filter_presets[filter_config_type]["min_sites"]
            top_positions_val = filter_presets[filter_config_type]["top_positions"]
            min_sites_top_val = filter_presets[filter_config_type]["min_sites_top_positions"]
        else:
            min_sites_val = min_sites
            top_positions_val = top_positions
            min_sites_top_val = min_sites_top
        
        filters = {
            "min_sites": min_sites_val,
            "top_positions": top_positions_val,
            "min_sites_top_positions": min_sites_top_val
        }
        
        # Show processing message
        with st.spinner("Traitement des données en cours..."):
            # Process data
            excel_data = process_data(uploaded_files, config, filters, create_specific_tabs)
            
            if excel_data:
                # Create download link
                b64 = base64.b64encode(excel_data.read()).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="analyse_semantique.xlsx" class="download-button">Télécharger le fichier Excel d\'analyse</a>'
                
                st.markdown("""
                <style>
                .download-button {
                    display: inline-block;
                    padding: 0.5em 1em;
                    color: white;
                    background-color: #4CAF50;
                    text-decoration: none;
                    border-radius: 4px;
                    font-weight: bold;
                    margin: 1em 0;
                }
                .download-button:hover {
                    background-color: #45a049;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(href, unsafe_allow_html=True)
                st.success("Analyse terminée avec succès ! Cliquez sur le bouton ci-dessus pour télécharger le fichier d'analyse.")
