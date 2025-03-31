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

# Function to detect columns in a dataframe
def detect_columns(df):
    """Tente de détecter automatiquement les colonnes importantes dans le DataFrame."""
    detected_columns = {
        "keyword": None,
        "volume": None,
        "position": None,
        "url": None
    }
    
    # Convertir les noms de colonnes en minuscules pour la comparaison
    df_cols_lower = [col.lower() for col in df.columns]
    
    # Dictionnaire des noms de colonnes possibles pour chaque type
    column_patterns = {
        "keyword": ["keyword", "mot-clé", "mot clé", "mot cle", "requête", "query", "phrase-clé", "search term", "terme de recherche"],
        "volume": ["volume", "search volume", "volume de recherche", "monthly volume", "volume mensuel", "global volume"],
        "position": ["position", "pos", "pos.", "positions", "ranking", "rank", "pos. moy.", "position moyenne"],
        "url": ["url", "target url", "url cible", "page", "url positionnée", "landing page", "ranking url", "page cible", "landing url"]
    }

    # Recherche exacte puis partielle
    for col_type, patterns in column_patterns.items():
        # Recherche exacte
        for i, col in enumerate(df_cols_lower):
            if col in patterns:
                detected_columns[col_type] = df.columns[i]
                break
        
        # Si pas trouvé, recherche partielle
        if detected_columns[col_type] is None:
            for i, col in enumerate(df_cols_lower):
                if any(pattern in col for pattern in patterns):
                    detected_columns[col_type] = df.columns[i]
                    break
    
    return detected_columns

# File uploader
uploaded_files = st.file_uploader("Importer les fichiers de données :", 
                                  type=["csv", "xlsx"], 
                                  accept_multiple_files=True)

# Try to detect file source if files are uploaded
source_detected = None
column_mapping = None

if uploaded_files:
    with st.spinner("Analyse des fichiers en cours..."):
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
            
            # Afficher les colonnes détectées pour aider au débogage
            st.write("Colonnes disponibles:", sample_df.columns.tolist())
            
            # Détecter les colonnes
            column_mapping = detect_columns(sample_df)
            
            # Déterminer la source probable
            col_lower = [col.lower() for col in sample_df.columns]
            if any('semrush' in col for col in col_lower):
                source_detected = "SEMrush"
            elif any('ahrefs' in col for col in col_lower):
                source_detected = "Ahrefs"
            elif 'query' in col_lower and 'page' in col_lower:
                source_detected = "Google Search Console"
            
            if source_detected:
                st.success(f"Source détectée: {source_detected}")
        except Exception as e:
            st.warning(f"Erreur lors de la détection automatique: {str(e)}")

# Configuration des colonnes
st.header("Configuration des colonnes")

column_config_options = ["Détection automatique", "SEMrush", "Ahrefs", "Google Search Console", "Custom"]
# Si une source a été détectée, la sélectionner par défaut
default_config_index = 0
if source_detected:
    try:
        default_config_index = column_config_options.index(source_detected)
    except ValueError:
        default_config_index = 0

column_config_type = st.selectbox(
    "Sélectionner un **type de configuration** :",
    column_config_options,
    index=default_config_index
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
    },
    "Détection automatique": {
        "keyword": column_mapping["keyword"] if column_mapping else "",
        "volume": column_mapping["volume"] if column_mapping else "",
        "position": column_mapping["position"] if column_mapping else "",
        "url": column_mapping["url"] if column_mapping else ""
    }
}

# Afficher les champs de saisie en fonction de la configuration sélectionnée
selected_config = config_presets[column_config_type]

col1, col2 = st.columns(2)
with col1:
    if column_config_type == "Custom":
        keyword_col = st.text_input("Colonne **Mot-clé** :")
        position_col = st.text_input("Colonne **Position** :")
    else:
        keyword_col = st.text_input("Colonne **Mot-clé** :", value=selected_config["keyword"])
        position_col = st.text_input("Colonne **Position** :", value=selected_config["position"])

with col2:
    if column_config_type == "Custom":
        volume_col = st.text_input("Colonne **Volume de recherche** :")
        url_col = st.text_input("Colonne **Page** :")
    else:
        volume_col = st.text_input("Colonne **Volume de recherche** :", value=selected_config["volume"])
        url_col = st.text_input("Colonne **Page** :", value=selected_config["url"])

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
    
    # Colonnes mappées pour chaque fichier
    file_columns = {}
    
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
            
            # Essayer de détecter automatiquement les colonnes si nécessaire
            if not keyword_column or not position_column or not url_column:
                detected_cols = detect_columns(df)
                file_keyword_col = keyword_column or detected_cols["keyword"]
                file_volume_col = volume_column or detected_cols["volume"]
                file_position_col = position_column or detected_cols["position"]
                file_url_col = url_column or detected_cols["url"]
                
                # Stocker le mapping pour ce fichier
                file_columns[file_name] = {
                    "keyword": file_keyword_col,
                    "volume": file_volume_col,
                    "position": file_position_col,
                    "url": file_url_col
                }
                
                # Informer l'utilisateur
                st.write(f"Colonnes détectées pour {file.name}:")
                st.write(f"- Mot-clé: {file_keyword_col}")
                st.write(f"- Position: {file_position_col}")
                st.write(f"- URL: {file_url_col}")
                if file_volume_col:
                    st.write(f"- Volume: {file_volume_col}")
            else:
                file_keyword_col = keyword_column
                file_volume_col = volume_column
                file_position_col = position_column
                file_url_col = url_column
                
                file_columns[file_name] = {
                    "keyword": file_keyword_col,
                    "volume": file_volume_col,
                    "position": file_position_col,
                    "url": file_url_col
                }
            
            # Check if required columns exist
            required_columns = [file_keyword_col, file_position_col, file_url_col]
            required_columns = [col for col in required_columns if col]  # Filtrer les valeurs vides
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.error(f"Colonnes manquantes dans {file.name}: {', '.join(missing_columns)}")
                continue
            
            # Add source column
            df['Source'] = file_name
            
            # Clean and normalize data
            df[file_keyword_col] = df[file_keyword_col].astype(str).str.lower().str.strip()
            df[file_keyword_col] = df[file_keyword_col].apply(lambda x: re.sub(r'\s+', ' ', x))
            
            # Ensure position column is numeric
            df[file_position_col] = pd.to_numeric(df[file_position_col], errors='coerce')
            
            # Clean URL if present
            if file_url_col in df.columns:
                df[file_url_col] = df[file_url_col].astype(str).str.lower()
                df[file_url_col] = df[file_url_col].apply(lambda x: re.sub(r'^https?://', '', x))
                df[file_url_col] = df[file_url_col].apply(lambda x: re.sub(r'/$', '', x))
            
            # Rename columns for consistency across files
            column_mapping = {
                file_keyword_col: "keyword",
                file_position_col: "position",
                file_url_col: "url"
            }
            
            if file_volume_col and file_volume_col in df.columns:
                column_mapping[file_volume_col] = "volume"
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Add to list of dataframes
            dfs[file_name] = df
            all_data.append(df)
            
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier {file.name}: {str(e)}")
    
    if not dfs:
        return None
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # Standardized column names
    std_keyword_col = "keyword"
    std_position_col = "position"
    std_url_col = "url"
    std_volume_col = "volume"
    
    # Process for semantic audit
    # 1. Group by keyword and count number of sites
    keyword_counts = combined_data.groupby(std_keyword_col)['Source'].nunique().reset_index()
    keyword_counts.columns = [std_keyword_col, 'Nombre de sites']
    
    # 2. Initialize filtered keywords based on settings
    if min_sites_filter > 0:
        filtered_keywords = keyword_counts[keyword_counts['Nombre de sites'] >= min_sites_filter]
    else:
        filtered_keywords = keyword_counts.copy()
    
    # 3. For each keyword, count sites in top X positions
    if top_x_positions > 0:
        top_positions_data = combined_data[combined_data[std_position_col] <= top_x_positions]
        top_positions_counts = top_positions_data.groupby(std_keyword_col)['Source'].nunique().reset_index()
        top_positions_counts.columns = [std_keyword_col, f'Nombre de sites dans le top {top_x_positions}']
        
        # Merge with filtered keywords
        filtered_keywords = pd.merge(filtered_keywords, top_positions_counts, on=std_keyword_col, how='left')
        filtered_keywords[f'Nombre de sites dans le top {top_x_positions}'].fillna(0, inplace=True)
        
        # Apply min_sites_top_x filter
        if min_sites_top_x > 0:
            filtered_keywords = filtered_keywords[
                filtered_keywords[f'Nombre de sites dans le top {top_x_positions}'] >= min_sites_top_x
            ]
    
    # 4. Add volume information if available
    if std_volume_col in combined_data.columns:
        # Take the max volume for each keyword (volumes might differ slightly between sources)
        volumes = combined_data.groupby(std_keyword_col)[std_volume_col].max().reset_index()
        filtered_keywords = pd.merge(filtered_keywords, volumes, on=std_keyword_col, how='left')
    
    # 5. Create position data for each source
    result_data = filtered_keywords.copy()
    
    for source_name, df in dfs.items():
        # Create a temporary dataframe with just keyword and position for this source
        temp_df = df[[std_keyword_col, std_position_col]].copy()
        temp_df.columns = [std_keyword_col, f'Position - {source_name}']
        
        # Merge with result data
        result_data = pd.merge(result_data, temp_df, on=std_keyword_col, how='left')
    
    # 6. Sort by number of sites and volume if available
    sort_columns = ['Nombre de sites']
    if top_x_positions > 0 and f'Nombre de sites dans le top {top_x_positions}' in result_data.columns:
        sort_columns.insert(0, f'Nombre de sites dans le top {top_x_positions}')
    
    if std_volume_col in result_data.columns:
        sort_columns.append(std_volume_col)
    
    result_data = result_data.sort_values(by=sort_columns, ascending=[False] * len(sort_columns))
    
    # 7. Create site summary data
    site_summaries = {}
    for site_name, df in dfs.items():
        summary = {}
        # Keyword count
        summary['Total mots-clés'] = len(df)
        
        # Positions breakdown
        positions = df[std_position_col].dropna()
        summary['Position moyenne'] = positions.mean() if not positions.empty else 0
        summary['Top 3'] = len(positions[positions <= 3])
        summary['Top 10'] = len(positions[positions <= 10])
        summary['Top 20'] = len(positions[positions <= 20])
        summary['Top 50'] = len(positions[positions <= 50])
        summary['Top 100'] = len(positions[positions <= 100])
        
        # Volume data if available
        if std_volume_col in df.columns:
            vol_data = df[std_volume_col].dropna()
            summary['Volume total'] = vol_data.sum() if not vol_data.empty else 0
            summary['Volume moyen'] = vol_data.mean() if not vol_data.empty else 0
            
            # Volume by position range
            summary['Volume Top 3'] = df[df[std_position_col] <= 3][std_volume_col].sum()
            summary['Volume Top 10'] = df[df[std_position_col] <= 10][std_volume_col].sum()
            summary['Volume Top 20'] = df[df[std_position_col] <= 20][std_volume_col].sum()
        
        site_summaries[site_name] = summary
    
    # 8. Create interest table (table des intérêts)
    # Interest table shows the volume distribution across position ranges for each site
    interest_data = []
    position_ranges = [(1, 3), (4, 10), (11, 20), (21, 50), (51, 100)]
    
    for site_name, df in dfs.items():
        site_row = {'Site': site_name}
        
        # Add interest metrics for each position range
        for start, end in position_ranges:
            range_df = df[(df[std_position_col] >= start) & (df[std_position_col] <= end)]
            
            # Keywords count in this range
            range_key = f"Mots-clés {start}-{end}"
            site_row[range_key] = len(range_df)
            
            # Volume in this range if available
            if std_volume_col in df.columns:
                vol_key = f"Volume {start}-{end}"
                site_row[vol_key] = range_df[std_volume_col].sum()
        
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
            presentation_ws.write(row + i, 0, site_name)
            presentation_ws.write(row + i, 1, len(dfs[site_name]))
        
        row += len(dfs) + 2
        
        # Add column mapping information
        presentation_ws.write(row, 0, 'Mapping des colonnes:', subtitle_format)
        row += 1
        
        for file_name, cols in file_columns.items():
            presentation_ws.write(row, 0, f"Fichier: {file_name}", subtitle_format)
            row += 1
            presentation_ws.write(row, 0, 'Colonne mot-clé:')
            presentation_ws.write(row, 1, cols["keyword"])
            row += 1
            
            presentation_ws.write(row, 0, 'Colonne position:')
            presentation_ws.write(row, 1, cols["position"])
            row += 1
            
            presentation_ws.write(row, 0, 'Colonne URL:')
            presentation_ws.write(row, 1, cols["url"])
            row += 1
            
            if cols["volume"]:
                presentation_ws.write(row, 0, 'Colonne volume:')
                presentation_ws.write(row, 1, cols["volume"])
                row += 1
            
            row += 1
        
        # Add filter information
        presentation_ws.write(row, 0, 'Paramètres de filtrage:', subtitle_format)
        row += 1
        presentation_ws.write(row, 0, 'Nombre minimum de sites:')
        presentation_ws.write(row, 1, min_sites_filter)
        row += 1
        
        if top_x_positions > 0:
            presentation_ws.write(row, 0, f'Position maximum (top):')
            presentation_ws.write(row, 1, top_x_positions)
            row += 1
            
            presentation_ws.write(row, 0, f'Minimum de sites dans le top:')
            presentation_ws.write(row, 1, min_sites_top_x)
            row += 1
        
        row += 2
        
        # Add global stats
        presentation_ws.write(row, 0, 'Statistiques globales:', subtitle_format)
        row += 1
        presentation_ws.write(row, 0, 'Nombre total de mots-clés analysés:')
        presentation_ws.write(row, 1, len(combined_data[std_keyword_col].unique()))
        row += 1
        
        presentation_ws.write(row, 0, 'Mots-clés après filtrage:')
        presentation_ws.write(row, 1, len(result_data))
        row += 1
        
        if std_volume_col in combined_data.columns:
            presentation_ws.write(row, 0, 'Volume total:')
            presentation_ws.write(row, 1, combined_data[std_volume_col].sum())
            row += 1
        
        # 2. Write "Liste de mots-clés & concurrence" sheet
        result_data.to_excel(writer, sheet_name='Liste de mots-clés & concurrence', index=False)
        keywords_ws = writer.sheets['Liste de mots-clés & concurrence']
        
        # Format the keywords worksheet
        keywords_ws.set_column('A:A', 30)  # Keyword column
        keywords_ws.set_column('B:Z', 15)  # Other columns
        
        # Apply header formatting
        for col_num, value in enumerate(result_data.columns.values):
            keywords_ws.write(0, col_num, value, header_format)
        
        # Add conditional formatting for position columns
        for col_num, column in enumerate(result_data.columns):
            if 'Position' in column:
                # Color scale from green (1) to red (>30)
                keywords_ws.conditional_format(1, col_num, len(result_data), col_num, {
                    'type': '3_color_scale',
                    'min_color': '#63BE7B',  # Green
                    'mid_color': '#FFEB84',  # Yellow
                    'max_color': '#F8696B',  # Red
                    'min_type': 'num',
                    'min_value': 1,
                    'mid_type': 'num',
                    'mid_value': 10,
                    'max_type': 'num',
                    'max_value': 30
                })
        
        # 3. Write "Table des intérêts" sheet
        interest_table.to_excel(writer, sheet_name='Table des intérêts', index=False)
        interest_ws = writer.sheets['Table des intérêts']
        
        # Format the interest table
        interest_ws.set_column('A:A', 25)  # Site column
        interest_ws.set_column('B:Z', 15)  # Other columns
        
        # Apply header formatting
        for col_num, value in enumerate(interest_table.columns.values):
            interest_ws.write(0, col_num, value, header_format)
        
        # 4. Write individual site sheets if requested
        if create_tabs:
            # First, write summary sheet with key metrics
            summary_data = pd.DataFrame.from_dict(site_summaries, orient='index').reset_index()
            summary_data.rename(columns={'index': 'Site'}, inplace=True)
            
            summary_data.to_excel(writer, sheet_name='Résumé par site', index=False)
            summary_ws = writer.sheets['Résumé par site']
            
            # Format the summary worksheet
            summary_ws.set_column('A:A', 25)  # Site column
            summary_ws.set_column('B:Z', 15)  # Other columns
            
            # Apply header formatting
            for col_num, value in enumerate(summary_data.columns.values):
                summary_ws.write(0, col_num, value, header_format)
            
            # Now write individual site sheets
            for site_name, df in dfs.items():
                sheet_name = site_name[:31]  # Excel sheet names limited to 31 chars
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                site_ws = writer.sheets[sheet_name]
                
                # Format worksheet
                site_ws.set_column('A:A', 30)  # Keyword column
                site_ws.set_column('B:Z', 15)  # Other columns
                
                # Apply header formatting
                for col_num, value in enumerate(df.columns.values):
                    site_ws.write(0, col_num, value, header_format)
                
                # Add position column formatting
                if std_position_col in df.columns:
                    pos_col = df.columns.get_loc(std_position_col)
                    site_ws.conditional_format(1, pos_col, len(df), pos_col, {
                        'type': '3_color_scale',
                        'min_color': '#63BE7B',  # Green
                        'mid_color': '#FFEB84',  # Yellow
                        'max_color': '#F8696B',  # Red
                        'min_type': 'num',
                        'min_value': 1,
                        'mid_type': 'num',
                        'mid_value': 10,
                        'max_type': 'num',
                        'max_value': 30
                    })
    
    output.seek(0)
    return output
