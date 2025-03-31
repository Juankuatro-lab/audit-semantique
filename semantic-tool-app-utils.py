import pandas as pd
import numpy as np
import re
from io import BytesIO
from typing import Dict, List, Tuple, Optional, Union


def clean_keyword(keyword: str) -> str:
    """Clean and normalize a keyword string."""
    if not isinstance(keyword, str):
        return ""
    
    # Convert to lowercase and strip whitespace
    keyword = keyword.lower().strip()
    
    # Remove extra spaces
    keyword = re.sub(r'\s+', ' ', keyword)
    
    # Remove special characters that don't add meaning
    keyword = re.sub(r'[^\w\s\'-]', '', keyword)
    
    return keyword


def clean_url(url: str) -> str:
    """Clean and normalize a URL string."""
    if not isinstance(url, str):
        return ""
    
    # Remove protocol (http://, https://)
    url = re.sub(r'^https?://', '', url)
    
    # Remove trailing slash
    url = re.sub(r'/$', '', url)
    
    # Convert to lowercase
    url = url.lower()
    
    return url


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    if not isinstance(url, str):
        return ""
    
    # Remove protocol
    url = re.sub(r'^https?://', '', url)
    
    # Get domain (everything before first slash)
    domain = url.split('/')[0]
    
    # Remove www. if present
    domain = re.sub(r'^www\.', '', domain)
    
    return domain


def read_keyword_file(file, file_format: str, column_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Read and process a keyword file with proper column mapping.
    
    Args:
        file: File object to read
        file_format: Format of the file ('csv' or 'xlsx')
        column_mapping: Dictionary mapping required columns to file columns
    
    Returns:
        Processed DataFrame
    """
    try:
        # Read file based on format
        if file_format == 'csv':
            df = pd.read_csv(file)
        elif file_format == 'xlsx':
            df = pd.read_excel(file)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        # Check if required columns exist
        required_columns = ['keyword', 'position', 'url']
        for req_col in required_columns:
            if req_col in column_mapping and column_mapping[req_col]:
                if column_mapping[req_col] not in df.columns:
                    raise ValueError(f"Required column '{column_mapping[req_col]}' not found in file")
            else:
                raise ValueError(f"Mapping for required column '{req_col}' is missing")
        
        # Create a new DataFrame with standardized columns
        result_df = pd.DataFrame()
        
        # Copy and rename columns based on mapping
        result_df['keyword'] = df[column_mapping['keyword']].apply(clean_keyword)
        result_df['position'] = pd.to_numeric(df[column_mapping['position']], errors='coerce')
        result_df['url'] = df[column_mapping['url']].apply(clean_url)
        
        # Add domain column
        result_df['domain'] = result_df['url'].apply(extract_domain)
        
        # Add volume if available
        if 'volume' in column_mapping and column_mapping['volume'] and column_mapping['volume'] in df.columns:
            result_df['volume'] = pd.to_numeric(df[column_mapping['volume']], errors='coerce')
        
        # Remove rows with missing critical data
        result_df = result_df.dropna(subset=['keyword', 'position'])
        
        return result_df
    
    except Exception as e:
        raise Exception(f"Error processing file: {str(e)}")


def analyze_competitive_keywords(
    dataframes: Dict[str, pd.DataFrame],
    min_sites: int = 2,
    top_positions: int = 10,
    min_sites_top: int = 1
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Analyze keywords across multiple sites to identify competitive opportunities.
    
    Args:
        dataframes: Dictionary of DataFrames with site name as key
        min_sites: Minimum number of sites that should rank for a keyword
        top_positions: Threshold for top positions
        min_sites_top: Minimum sites in top positions
    
    Returns:
        Tuple containing:
            - Summary DataFrame with competitive analysis
            - Detailed DataFrame with position data for each site
    """
    if not dataframes:
        return pd.DataFrame(), pd.DataFrame()
    
    # Combine all dataframes
    all_data = []
    for site_name, df in dataframes.items():
        df_copy = df.copy()
        df_copy['site'] = site_name
        all_data.append(df_copy)
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Count sites per keyword
    keyword_counts = combined_df.groupby('keyword')['site'].nunique().reset_index()
    keyword_counts.columns = ['keyword', 'sites_count']
    
    # Initialize filtered keywords DataFrame
    if min_sites > 0:
        # Filter by minimum sites
        filtered_keywords = keyword_counts[keyword_counts['sites_count'] >= min_sites]
    else:
        # If min_sites is 0, include all keywords
        filtered_keywords = keyword_counts
    
    # Count sites in top positions
    if top_positions > 0 and min_sites_top > 0:
        top_positions_df = combined_df[combined_df['position'] <= top_positions]
        top_counts = top_positions_df.groupby('keyword')['site'].nunique().reset_index()
        top_counts.columns = ['keyword', f'sites_in_top_{top_positions}']
        
        # Merge with filtered keywords
        filtered_keywords = pd.merge(filtered_keywords, top_counts, on='keyword', how='left')
        filtered_keywords[f'sites_in_top_{top_positions}'].fillna(0, inplace=True)
        
        # Apply min_sites_top filter
        filtered_keywords = filtered_keywords[
            filtered_keywords[f'sites_in_top_{top_positions}'] >= min_sites_top
        ]
    
    # Get volume data if available
    if 'volume' in combined_df.columns:
        # Take maximum volume for each keyword (volumes might differ slightly between sources)
        volumes = combined_df.groupby('keyword')['volume'].max().reset_index()
        filtered_keywords = pd.merge(filtered_keywords, volumes, on='keyword', how='left')
    
    # Create detailed positional data
    if not filtered_keywords.empty:
        # Get list of keywords that passed filters
        target_keywords = filtered_keywords['keyword'].tolist()
        
        # Filter combined data to only these keywords
        filtered_data = combined_df[combined_df['keyword'].isin(target_keywords)]
        
        # Create pivot table with positions for each site
        positions_pivot = filtered_data.pivot_table(
            index='keyword', 
            columns='site', 
            values='position', 
            aggfunc='min'  # If a keyword appears multiple times for a site, take the best position
        ).reset_index()
        
        # Rename columns to be more descriptive
        positions_pivot.columns.name = None
        for col in positions_pivot.columns:
            if col != 'keyword':
                positions_pivot.rename(columns={col: f'Position - {col}'}, inplace=True)
        
        # Merge summary data with positional data
        result = pd.merge(filtered_keywords, positions_pivot, on='keyword', how='left')
        
        # Add additional columns for analysis
        if top_positions > 0:
            # Add column showing number of sites in top X
            if f'sites_in_top_{top_positions}' not in result.columns:
                # Calculate it if not already present
                for col in result.columns:
                    if col.startswith('Position - '):
                        result[f'In_Top_{top_positions}_{col[11:]}'] = result[col].apply(
                            lambda x: 1 if pd.notnull(x) and x <= top_positions else 0
                        )
                
                # Sum to get total sites in top X
                top_cols = [col for col in result.columns if col.startswith(f'In_Top_{top_positions}_')]
                result[f'sites_in_top_{top_positions}'] = result[top_cols].sum(axis=1)
                
                # Clean up temporary columns
                for col in top_cols:
                    del result[col]
        
        # Sort by sites count and then by volume if available
        sort_columns = ['sites_count']
        if top_positions > 0 and f'sites_in_top_{top_positions}' in result.columns:
            sort_columns.insert(0, f'sites_in_top_{top_positions}')
        
        if 'volume' in result.columns:
            sort_columns.append('volume')
        
        result.sort_values(by=sort_columns, ascending=[False] * len(sort_columns), inplace=True)
        
        return result, filtered_data
    
    return pd.DataFrame(), pd.DataFrame()


def create_excel_report(
    summary_df: pd.DataFrame,
    detailed_df: pd.DataFrame,
    site_dataframes: Dict[str, pd.DataFrame],
    create_site_tabs: bool = True
) -> BytesIO:
    """
    Create an Excel report with the semantic audit results.
    
    Args:
        summary_df: DataFrame with the competitive analysis summary
        detailed_df: DataFrame with detailed keyword data
        site_dataframes: Dictionary of original site DataFrames
        create_site_tabs: Whether to create tabs for each site's data
    
    Returns:
        BytesIO object containing the Excel file
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Create formats
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
        
        # Write summary sheet
        if not summary_df.empty:
            summary_df.to_excel(writer, sheet_name='Analyse concurrentielle', index=False)
            
            # Format the sheet
            worksheet = writer.sheets['Analyse concurrentielle']
            
            # Set column widths
            worksheet.set_column('A:A', 30)  # Keyword column
            worksheet.set_column('B:Z', 15)  # Other columns
            
            # Apply header formatting
            for col_num, value in enumerate(summary_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Add conditional formatting for position columns
            for col_num, column in enumerate(summary_df.columns):
                if 'Position' in column:
                    # Color scale from green (1) to red (>10)
                    worksheet.conditional_format(1, col_num, len(summary_df), col_num, {
                        'type': '3_color_scale',
                        'min_color': '#63BE7B',  # Green
                        'mid_color': '#FFEB84',  # Yellow
                        'max_color': '#F8696B',  # Red
                        'min_type': 'num',
                        'min_value': 1,
                        'mid_type': 'num',
                        'mid_value': 5,
                        'max_type': 'num',
                        'max_value': 10
                    })
        
        # Write detailed keyword data
        if not detailed_df.empty:
            pivot_df = detailed_df.pivot_table(
                index=['keyword', 'site'], 
                values=['position', 'url'], 
                aggfunc={'position': 'min', 'url': 'first'}
            ).reset_index()
            
            pivot_df.to_excel(writer, sheet_name='Données détaillées', index=False)
            
            worksheet = writer.sheets['Données détaillées']
            worksheet.set_column('A:A', 30)  # Keyword column
            worksheet.set_column('B:B', 20)  # Site column
            worksheet.set_column('C:C', 15)  # Position column
            worksheet.set_column('D:D', 50)  # URL column
            
            # Apply header formatting
            for col_num, value in enumerate(pivot_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        # Write individual site tabs if requested
        if create_site_tabs and site_dataframes:
            for site_name, df in site_dataframes.items():
                # Limit sheet name to 31 characters (Excel limit)
                sheet_name = site_name[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                worksheet = writer.sheets[sheet_name]
                
                # Set column widths
                for col_num, column in enumerate(df.columns):
                    if 'keyword' in column.lower():
                        worksheet.set_column(col_num, col_num, 30)
                    elif 'url' in column.lower():
                        worksheet.set_column(col_num, col_num, 50)
                    else:
                        worksheet.set_column(col_num, col_num, 15)
                
                # Apply header formatting
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
    
    output.seek(0)
    return output
