import streamlit as st
import pandas as pd
import numpy as np
import io
import base64
import re
from pathlib import Path
import os
from datetime import datetime

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
</style>
""", unsafe_allow_html=True)

# Fonction pour détecter automatiquement les colonnes
def detect_columns(df):
    """Tente de détecter automatiquement les colonnes importantes dans le DataFrame."""
    detected_columns = {
        "keyword": None,
        "volume": None,
        "position": None,
        "url": None
    }
    
    # Dictionnaire des noms de colonnes possibles pour chaque type
    column_options = {
        "keyword": ["keyword", "keywords", "mot-clé", "mot clé", "mot cle", "requête", "query", "phrase-clé", "search term"],
        "volume": ["volume", "search volume", "volume de recherche", "monthly volume", "global volume", "sv", "vol.", "vol"],
        "position": ["position", "pos", "pos.", "positions", "ranking", "rank", "pos. moy.", "position moyenne", "current rank"],
        "url": ["url", "target url", "url cible", "page", "url positionnée", "landing page", "ranking url", "url ranking", "top ranking page"]
    }
    
    # Convertir toutes les colonnes en minuscules pour la comparaison
    df_columns_lower = [col.lower() for col in df.columns]
    
    # Vérifier chaque type de colonne
    for col_type, options in column_options.items():
        for i, col in enumerate(df_columns_lower):
            # Vérifier si la colonne correspond exactement ou contient un des mots clés
            if col in options or any(option in col for option in options):
                detected_columns[col_type] = df.columns[i]
                break
    
    return detected_columns

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
    ["Détection automatique", "SEMrush", "Ahrefs", "Google Search Console", "Custom"]
)

# Définir les configurations prédéfinies
config_presets = {
    "SEMrush": {
        "keyword": "Mot-clé",  # En français souvent "Mot-clé"
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
        "keyword": "Query",    # "Requête" en français
        "volume": "",          # GSC n'a pas de données de volume
        "position": "Position",
        "url": "Page"
    },
    "Custom": {
        "keyword": "",
        "volume": "",
        "position": "",
        "url": ""
    },
    "Détection automatique": {
        "keyword": "",
        "volume": "",
        "position": "",
        "url": ""
    }
}

# Variables pour stocker les colonnes sélectionnées
keyword_col = ""
volume_col = ""
position_col = ""
url_col = ""

# Afficher les champs de saisie en fonction de la configuration sélectionnée
if column_config_type == "Détection automatique":
    st.info("L'outil tentera de détecter automatiquement les colonnes appropriées dans vos fichiers.")
    
    # Tenter de détecter les colonnes si des fichiers ont été chargés
    if uploaded_files:
        with st.spinner("Analyse du premier fichier pour détecter les colonnes..."):
            try:
                # Lire le premier fichier pour détecter les colonnes
                first_file = uploaded_files[0]
                file_extension = first_file.name.split('.')[-1].lower()
                
                if file_extension == 'csv':
                    sample_df = pd.read_csv(first_file)
                elif file_extension == 'xlsx':
                    sample_df = pd.read_excel(first_file)
                
                # Réinitialiser le pointeur du fichier pour une utilisation ultérieure
                first_file.seek(0)
                
                # Détecter les colonnes
                detected_cols = detect_columns(sample_df)
                
                # Afficher les colonnes détectées
                st.write("Colonnes détectées dans le fichier:")
                st.write(f"- Colonnes disponibles: {list(sample_df.columns)}")
                st.write(f"- Mot-clé: {detected_cols['keyword']}")
                st.write(f"- Position: {detected_cols['position']}")
                st.write(f"- URL: {detected_cols['url']}")
                if detected_cols['volume']:
                    st.write(f"- Volume: {detected_cols['volume']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    keyword_col = st.text_input("Colonne **Mot-clé** :", value=detected_cols["keyword"] or "")
                    position_col = st.text_input("Colonne **Position** :", value=detected_cols["position"] or "")
                with col2:
                    volume_col = st.text_input("Colonne **Volume de recherche** :", value=detected_cols["volume"] or "")
                    url_col = st.text_input("Colonne **Page** :", value=detected_cols["url"] or "")
                
                # Message informatif
                if all(detected_cols.values()):
                    st.success("Toutes les colonnes nécessaires ont été détectées automatiquement.")
                elif any(detected_cols.values()):
                    st.warning("Certaines colonnes ont été détectées. Veuillez vérifier et compléter les colonnes manquantes.")
                else:
                    st.error("Aucune colonne n'a pu être détectée automatiquement. Veuillez les spécifier manuellement.")
            
            except Exception as e:
                st.error(f"Erreur lors de la détection automatique des colonnes: {str(e)}")
                col1, col2 = st.columns(2)
                with col1:
                    keyword_col = st.text_input("Colonne **Mot-clé** :")
                    position_col = st.text_input("Colonne **Position** :")
                with col2:
                    volume_col = st.text_input("Colonne **Volume de recherche** :")
                    url_col = st.text_input("Colonne **Page** :")
    else:
        st.warning("Veuillez importer au moins un fichier pour la détection automatique des colonnes.")
        col1, col2 = st.columns(2)
        with col1:
            keyword_col = st.text_input("Colonne **Mot-clé** :")
            position_col = st.text_input("Colonne **Position** :")
        with col2:
            volume_col = st.text_input("Colonne **Volume de recherche** :")
            url_col = st.text_input("Colonne **Page** :")
elif column_config_type == "Custom":
    col1, col2 = st.columns(2)
    with col1:
        keyword_col = st.text_input("Colonne **Mot-clé** :")
        position_col = st.text_input("Colonne **Position** :")
    with col2:
        volume_col = st.text_input("Colonne **Volume de recherche** :")
        url_col = st.text_input("Colonne **Page** :")
else:
    selected_config = config_presets[column_config_type]
    keyword_col = selected_config["keyword"]
    volume_col = selected_config["volume"]
    position_col = selected_config["position"]
    url_col = selected_config["url"]
    
    col1, col2 = st.columns(2)
    with col1:
        keyword_col = st.text_input("Colonne **Mot-clé** :", value=keyword_col)
        position_col = st.text_input("Colonne **Position** :", value=position_col)
    with col2:
        volume_col = st.text_input("Colonne **Volume de recherche** :", value=volume_col)
        url_col = st.text_input("Colonne **Page** :", value=url_col)

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
    
    # Variables pour suivre l'auto-détection
    is_autodetect = column_config_type == "Détection automatique"
    file_configs = {}
    
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
            
            # Si c'est en détection automatique, détecter les colonnes pour ce fichier
            if is_autodetect:
                detected = detect_columns(df)
                file_configs[file_name] = {
                    "keyword": detected["keyword"],
                    "volume": detected["volume"],
                    "position": detected["position"],
                    "url": detected["url"]
                }
                
                # Afficher les colonnes détectées
                st.info(f"Colonnes détectées pour {file.name}:")
                st.write(f"- Mot-clé: {detected['keyword']}")
                st.write(f"- Position: {detected['position']}")
                st.write(f"- URL: {detected['url']}")
                if detected['volume']:
                    st.write(f"- Volume: {detected['volume']}")
                
                # Vérifier si les colonnes requises sont détectées
                if not detected["keyword"] or not detected["position"]:
                    st.error(f"Impossible de détecter toutes les colonnes nécessaires dans {file.name}")
                    st.write(f"Colonnes disponibles: {list(df.columns)}")
                    continue
                
                # Utiliser les colonnes détectées pour ce fichier
                kw_col = detected["keyword"]
                vol_col = detected["volume"]
                pos_col = detected["position"]
                url_col = detected["url"]
            else:
                # Utiliser les colonnes spécifiées
                kw_col = keyword_column
                vol_col = volume_column
                pos_col = position_column
                url_col = url_column
            
            # Vérifier si les colonnes requises existent
            required_columns = [kw_col, pos_col]
            if url_col:
                required_columns.append(url_col)
                
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.error(f"Colonnes manquantes dans {file.name}: {', '.join(missing_columns)}")
                st.write(f"Colonnes disponibles: {list(df.columns)}")
                continue
            
            # Add source column
            df['Source'] = file_name
            
            # Clean and normalize data
            df[kw_col] = df[kw_col].astype(str).str.lower().str.strip()
            df[kw_col] = df[kw_col].apply(lambda x: re.sub(r'\s+', ' ', x))
            
            # Ensure position column is numeric
            df[pos_col] = pd.to_numeric(df[pos_col], errors='coerce')
            
            # Clean URL if present
            if url_col and url_col in df.columns:
                df[url_col] = df[url_col].astype(str).str.lower()
                df[url_col] = df[url_col].apply(lambda x: re.sub(r'^https?://', '', x))
                df[url_col] = df[url_col].apply(lambda x: re.sub(r'/$', '', x))
            
            # Standardize column names for merging later
            # Créer une copie du DataFrame avec des noms de colonnes standardisés
            standardized_df = df.copy()
            
            # Renommer les colonnes à des noms standardisés
            column_mapping = {}
            if kw_col:
                column_mapping[kw_col] = 'keyword_std'
            if pos_col:
                column_mapping[pos_col] = 'position_std'
            if vol_col and vol_col in df.columns:
                column_mapping[vol_col] = 'volume_std'
            if url_col and url_col in df.columns:
                column_mapping[url_col] = 'url_std'
            
            standardized_df.rename(columns=column_mapping, inplace=True)
            
            # Conserver les informations de mapping pour ce fichier
            file_configs[file_name] = {
                "original_df": df,
                "standardized_df": standardized_df,
                "mapping": {
                    "keyword": kw_col,
                    "position": pos_col,
                    "volume": vol_col if vol_col and vol_col in df.columns else None,
                    "url": url_col if url_col and url_col in df.columns else None
                }
            }
            
            # Add to list of dataframes
            dfs[file_name] = standardized_df
            all_data.append(standardized_df)
            
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier {file.name}: {str(e)}")
    
    if not dfs:
        return None
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # Process for semantic audit
    # 1. Group by keyword and count number of sites
    keyword_counts = combined_data.groupby('keyword_std')['Source'].nunique().reset_index()
    keyword_counts.columns = ['keyword_std', 'Nombre de sites']
    
    # 2. Initialize filtered keywords based on settings
    if min_sites_filter > 0:
        filtered_keywords = keyword_counts[keyword_counts['Nombre de sites'] >= min_sites_filter]
    else:
        filtered_keywords = keyword_counts.copy()
    
    # 3. For each keyword, count sites in top X positions
    if top_x_positions > 0:
        top_positions_data = combined_data[combined_data['position_std'] <= top_x_positions]
        top_positions_counts = top_positions_data.groupby('keyword_std')['Source'].nunique().reset_index()
        top_positions_counts.columns = ['keyword_std', f'Nombre de sites dans le top {top_x_positions}']
        
        # Merge with filtered keywords
        filtered_keywords = pd.merge(filtered_keywords, top_positions_counts, on='keyword_std', how='left')
        filtered_keywords[f'Nombre de sites dans le top {top_x_positions}'].fillna(0, inplace=True)
        
        # Apply min_sites_top_x filter
        if min_sites_top_x > 0:
            filtered_keywords = filtered_keywords[
                filtered_keywords[f'Nombre de sites dans le top {top_x_positions}'] >= min_sites_top_x
            ]
    
    # 4. Add volume information if available
    if 'volume_std' in combined_data.columns:
        # Take the max volume for each keyword (volumes might differ slightly between sources)
        volumes = combined_data.groupby('keyword_std')['volume_std'].max().reset_index()
        filtered_keywords = pd.merge(filtered_keywords, volumes, on='keyword_std', how='left')
    
    # 5. Create position data for each source
    result_data = filtered_keywords.copy()
    
    for source_name, df in dfs.items():
        # Create a temporary dataframe with just keyword and position for this source
        temp_df = df[['keyword_std', 'position_std']].copy()
        temp_df.columns = ['keyword_std', f'Position - {source_name}']
        
        # Merge with result data
        result_data = pd.merge(result_data, temp_df, on='keyword_std', how='left')
    
    # 6. Sort by number of sites and volume if available
    sort_columns = ['Nombre de sites']
    if top_x_positions > 0 and f'Nombre de sites dans le top {top_x_positions}' in result_data.columns:
        sort_columns.insert(0, f'Nombre de sites dans le top {top_x_positions}')
    
    if 'volume_std' in result_data.columns:
        sort_columns.append('volume_std')
    
    result_data = result_data.sort_values(by=sort_columns, ascending=[False] * len(sort_columns))
    
    # 7. Create site summary data
    site_summaries = {}
    for site_name, df in dfs.items():
        summary = {}
        # Keyword count
        summary['Total mots-clés'] = len(df)
        
        # Positions breakdown
        positions = df['position_std'].dropna()
        summary['Position moyenne'] = positions.mean() if not positions.empty else 0
        summary['Top 3'] = len(positions[positions <= 3])
        summary['Top 10'] = len(positions[positions <= 10])
        summary['Top 20'] = len(positions[positions <= 20])
        summary['Top 50'] = len(positions[positions <= 50])
        summary['Top 100'] = len(positions[positions <= 100])
        
        # Volume data if available
        if 'volume_std' in df.columns:
            vol_data = df['volume_std'].dropna()
            summary['Volume total'] = vol_data.sum() if not vol_data.empty else 0
            summary['Volume moyen'] = vol_data.mean() if not vol_data.empty else 0
            
            # Volume by position range
            summary['Volume Top 3'] = df[df['position_std'] <= 3]['volume_std'].sum()
            summary['Volume Top 10'] = df[df['position_std'] <= 10]['volume_std'].sum()
            summary['Volume Top 20'] = df[df['position_std'] <= 20]['volume_std'].sum()
        
        site_summaries[site_name] = summary
    
    # 8. Create interest table (table des intérêts)
    # Interest table shows the volume distribution across position ranges for each site
    interest_data = []
    position_ranges = [(1, 3), (4, 10), (11, 20), (21, 50), (51, 100)]
    
    for site_name, df in dfs.items():
        site_row = {'Site': site_name}
        
        # Add interest metrics for each position range
        for start, end in position_ranges:
            range_df = df[(df['position_std'] >= start) & (df['position_std'] <= end)]
            
            # Keywords count in this range
            range_key = f"Mots-clés {start}-{end}"
            site_row[range_key] = len(range_df)
            
            # Volume in this range if available
            if 'volume_std' in df.columns:
                vol_key = f"Volume {start}-{end}"
                site_row[vol_key] = range_df['volume_std'].sum()
        
        interest_data.append(site_row)
    
    interest_table = pd.DataFrame(interest_data)
    
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
            'num_format': '#,##0',
            'border': 1
        })
        
        percent_format = workbook.add_format({
            'num_format': '0.00%',
            'border': 1
        })
        
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'font_color': '#4B88B6'
        })
        
        subtitle_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'font_color': '#4B88B6'
        })
        
        normal_format = workbook.add_format({
            'border': 1
        })
        
        # 1. Create Presentation sheet
        presentation_ws = workbook.add_worksheet('Présentation')
        
        # Set column widths
        presentation_ws.set_column('A:A', 30)
        presentation_ws.set_column('B:E', 15)
        
        # Add title and info
        row = 0
        presentation_ws.write(row, 0, 'Audit Sémantique', title_format)
        row += 2
        
        # Add date information
        today = datetime.now().strftime('%d/%m/%Y')
        presentation_ws.write(row, 0, 'Date de génération:', subtitle_format)
        presentation_ws.write(row, 1, today)
        row += 2
        
        # Add summary of files processed
        presentation_ws.write(row, 0, 'Fichiers traités:', subtitle_format)
        row += 1
        for i, site_name in enumerate(dfs.keys()):
            presentation_ws.write(row + i, 0, site_name
