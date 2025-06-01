import streamlit as st
import pandas as pd
import numpy as np
import os # Added import
from global_analyzer import analyze_ad_sets # Removed calculate_kpis_for_analysis import as it's not directly used here
from bv5_analyzer import analyze_ad_sets_bv5 # Added import for BV5
from bv5_may23_analyzer import analyze_ad_sets as analyze_ad_sets_bv5_may23_specific # Changed import with alias
from tt_bv2_may23_analyzer import analyze_ad_sets as analyze_ad_sets_tt_bv2_may23_specific # Changed import with alias

st.set_page_config(layout="wide")

country_code_to_name_map = {
    "TR": "Turkey",
    "AZ": "Azerbaijan",
    "US": "United States",
    "DE": "Germany",
    "GB": "United Kingdom",
    "UZ": "Uzbekistan",
    "CA": "Canada",
    "AU": "Australia",
    "FR": "France",
    "NL": "Netherlands",
    "AE": "United Arab Emirates",
    # İhtiyaç duyuldukça daha fazla ülke eklenebilir
}

# --- Global Helper Functions ---

def get_original_row_count(file_name_in_data_dir):
    r"""Reads a CSV file from the 'data' directory and returns the number of rows (excluding header)."""
    try:
        # Construct path relative to this script's directory, then go up and into 'data'
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir) # Go up one level from 'src' to project root
        absolute_file_path = os.path.join(project_root, 'data', file_name_in_data_dir)
        
        df = pd.read_csv(absolute_file_path)
        return len(df)
    except FileNotFoundError:
        st.error(f"Error in get_original_row_count: File not found at '{os.path.join('data', file_name_in_data_dir)}' (tried absolute path: {absolute_file_path})")
        return 0
    except Exception as e:
        st.error(f"Error reading '{os.path.join('data', file_name_in_data_dir)}' in get_original_row_count: {e}")
        return 0

def display_cleaning_info(original_rows, cleaned_rows, dataset_name):
    r"""Displays information about the data cleaning process."""
    if original_rows > 0:
        removed_rows = original_rows - cleaned_rows
        st.subheader(f"Veri Temizleme Süreci ({dataset_name})")
        st.markdown(f"""
        - Orijinal veri setinde **{original_rows:,} satır** bulunuyordu.
        - Temizlik işlemi (ülke bilgisi olmayan satırların çıkarılması) sonucunda **{removed_rows:,} satır çıkarılarak** veri seti **{cleaned_rows:,} satıra** düşürüldü.
        """)
    else:
        st.markdown(f"Temizlenmiş {dataset_name} verisi için {cleaned_rows:,} satır bulundu. Orijinal satır sayısı alınamadı.")
    st.divider()

def column_formatters():
    r"""Returns a dictionary of column formatters for DataFrames."""
    return {
        "Total Spent (USD)": "${:,.2f}",
        "Total Reach": "{:,.0f}",
        "Total Impressions": "{:,.0f}",
        "Total Link Clicks": "{:,.0f}",
        "Total Results": "{:,.0f}",
        "CTR (%)": "{:.2f}%",
        "CPC (USD)": "${:,.2f}",
        "CPM (USD)": "${:,.2f}",
        "Avg. Cost per Result (USD)": "${:,.2f}",
        # For global average table
        "Toplam Harcama (USD)": "${:,.2f}",
        "Toplam Reach": "{:,.0f}",
        "Toplam Gösterim (Impressions)": "{:,.0f}",
        "Toplam Link Tıklaması": "{:,.0f}",
        "Toplam Sonuç (Results)": "{:,.0f}",
        "Ortalama CTR (%)": "{:.2f}%",
        "Ortalama CPC (USD)": "${:,.2f}",
        "Ortalama CPM (USD)": "${:,.2f}",
        "Ortalama Sonuç Başına Maliyet (USD)": "${:,.2f}",
    }

def prepare_country_kpis(df_cleaned, dataset_name="Dataset"):
    r"""Prepares and calculates country-level KPIs from a cleaned DataFrame."""
    if df_cleaned is None or df_cleaned.empty:
        st.warning(f"Cannot prepare country KPIs for {dataset_name}: Input data is empty or None.")
        return pd.DataFrame()

    df_processed = calculate_kpis_for_display(df_cleaned.copy())

    country_summary_agg = df_processed.groupby('Country').agg(
        total_spent=('Amount spent (USD)', 'sum'),
        total_impressions=('Impressions', 'sum'),
        total_link_clicks=('Link clicks', 'sum'),
        total_reach=('Reach', 'sum'),
        total_results=('Results', 'sum')
    ).reset_index()

    country_summary_for_kpis = country_summary_agg.rename(columns={
        'total_spent': 'Amount spent (USD)',
        'total_impressions': 'Impressions',
        'total_link_clicks': 'Link clicks',
        'total_reach': 'Reach',
        'total_results': 'Results'
    })
    country_summary_kpis = calculate_kpis_for_display(country_summary_for_kpis)
    country_summary_kpis['Avg. Cost per Result (USD)'] = np.where(
        country_summary_kpis['Results'] > 0,
        country_summary_kpis['Amount spent (USD)'] / country_summary_kpis['Results'], 0)
    
    country_summary_kpis = country_summary_kpis.rename(columns={
        'Amount spent (USD)': 'Total Spent (USD)',
        'Impressions': 'Total Impressions',
        'Link clicks': 'Total Link Clicks',
        'Reach': 'Total Reach',
        'Results': 'Total Results'
    }).sort_values(by='Total Spent (USD)', ascending=False)
    
    # Map country codes to names for display
    country_summary_kpis_display = country_summary_kpis.copy()
    country_summary_kpis_display['Country'] = country_summary_kpis_display['Country'].map(country_code_to_name_map).fillna(country_summary_kpis_display['Country'])
    
    return country_summary_kpis_display

# Generic function to display ad set analysis tables
def display_ad_set_analysis(df_processed, analyze_function, dataset_label_short, top_n_ad_sets=10):
    r"""
    Displays ad set analysis tables for TR, AZ, and Global (excluding TR, AZ).
    
    Args:
        df_processed (pd.DataFrame): The processed DataFrame with KPIs, ready for ad set analysis.
        analyze_function (callable): The specific analysis function to call (e.g., analyze_ad_sets_bv5).
        dataset_label_short (str): A short label for the dataset (e.g., "BV5", "BV2 May 23-29").
        top_n_ad_sets (int): Number of top ad sets to display.
    """
    if df_processed is None or df_processed.empty or 'Ad Set Name' not in df_processed.columns:
        st.warning(f"`Ad Set Name` sütunu {dataset_label_short} veri setinde bulunamadı veya veri boş. Reklam seti analizi yapılamıyor.")
        return

    tr_name = country_code_to_name_map.get('TR', 'TR')
    az_name = country_code_to_name_map.get('AZ', 'AZ')
    
    cols_to_display_ad_sets = ['Ad Set Name', 'Total Spent (USD)', 'Total Reach', 'Total Link Clicks', 'Total Results', 'CTR (%)', 'CPC (USD)', 'CPM (USD)', 'Avg. Cost per Result (USD)']
    style_format_ad_sets = column_formatters() # Use the global formatter

    st.header(f"Reklam Seti Bazlı KPI Analizleri ({dataset_label_short})")

    # Helper for displaying individual ad set tables
    def _display_single_ad_set_table_set(results_df, spent_df, label_suffix):
        full_label = f"{label_suffix} ({dataset_label_short})"
        st.markdown(f"##### En Çok Sonuç Getiren İlk {top_n_ad_sets} Reklam Seti ({full_label})")
        if results_df is not None and not results_df.empty:
            st.dataframe(results_df[cols_to_display_ad_sets].style.format(style_format_ad_sets), use_container_width=True)
        else:
            st.info(f"Sonuçlara göre sıralanacak reklam seti bulunamadı ({full_label}).")
        
        st.markdown(f"##### En Çok Harcama Yapan İlk {top_n_ad_sets} Reklam Seti ({full_label})")
        if spent_df is not None and not spent_df.empty:
            st.dataframe(spent_df[cols_to_display_ad_sets].style.format(style_format_ad_sets), use_container_width=True)
        else:
            st.info(f"Harcamalara göre sıralanacak reklam seti bulunamadı ({full_label}).")
        st.caption(f"Not: Yukarıdaki reklam seti analizleri {full_label} için geçerlidir.")
        st.divider()

    st.markdown(f"#### {tr_name} Reklam Seti Performansı")
    tr_results_df, tr_spent_df = analyze_function(df_processed, target_countries=['TR'], filter_type='include', top_n=top_n_ad_sets)
    _display_single_ad_set_table_set(tr_results_df, tr_spent_df, tr_name)

    st.markdown(f"#### {az_name} Reklam Seti Performansı")
    az_results_df, az_spent_df = analyze_function(df_processed, target_countries=['AZ'], filter_type='include', top_n=top_n_ad_sets)
    _display_single_ad_set_table_set(az_results_df, az_spent_df, az_name)
    
    global_label_suffix = f"Global ({tr_name} ve {az_name} Hariç)"
    st.markdown(f"#### {global_label_suffix} Reklam Seti Performansı")
    global_results_df, global_spent_df = analyze_function(df_processed, target_countries=['TR', 'AZ'], filter_type='exclude', top_n=top_n_ad_sets)
    _display_single_ad_set_table_set(global_results_df, global_spent_df, global_label_suffix)

# Renamed to avoid conflict and clarify its scope for app-level display needs (e.g., country summaries)
def calculate_kpis_for_display(df):
    kpi_df = df.copy()
    cols_to_numerify = ['Amount spent (USD)', 'Impressions', 'Link clicks', 'Reach', 'Results']
    for col in cols_to_numerify:
        if col in kpi_df.columns:
            kpi_df[col] = pd.to_numeric(kpi_df[col], errors='coerce').fillna(0)
        else:
            st.warning(f"Expected column '{col}' not found in calculate_kpis_for_display. It will be initialized to 0.")
            kpi_df[col] = 0

    kpi_df['CTR (%)'] = np.where(kpi_df['Impressions'] > 0, (kpi_df['Link clicks'] / kpi_df['Impressions']) * 100, 0)
    kpi_df['CPC (USD)'] = np.where(kpi_df['Link clicks'] > 0, kpi_df['Amount spent (USD)'] / kpi_df['Link clicks'], 0)
    kpi_df['CPM (USD)'] = np.where(kpi_df['Impressions'] > 0, (kpi_df['Amount spent (USD)'] / kpi_df['Impressions']) * 1000, 0)
    return kpi_df

# Load data
@st.cache_data # Use Streamlit's caching to load data efficiently
def load_data(file_path):
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"Hata: '{file_path}' dosyası bulunamadı. Lütfen dosyanın 'data' klasöründe olduğundan emin olun.")
        return None
    except Exception as e:
        st.error(f"'{file_path}' okunurken bir hata oluştu: {e}")
        return None

# Paths to the data files
cleaned_bv2_file = 'data/clean_global.csv'
original_bv2_file_name = 'BV2-All-10-22 May-Dataları-Global.csv' # For display purposes
bv5_file_name = 'BV5-All-report-May-10-2025-to-May-22-2025.csv' # For display purposes

cleaned_bv5_file = 'data/clean_bv5_global.csv' # Path for cleaned BV5 data
original_bv5_file_name = 'BV5-All-report-May-10-2025-to-May-22-2025.csv' # For display

cleaned_bv5_may23_file = 'data/clean_bv5_may23_global.csv' # Path for cleaned BV5 May 23-29 data
original_bv5_may23_file_name = 'BV5-May-23-2025-to-May-29-2025.csv' # For display

cleaned_tt_bv2_may23_file = 'data/clean_tt_bv2_may23_global.csv' # Path for cleaned TT BV2 May 23-29 data
original_tt_bv2_may23_file_name = 'TT-Reklam-Dataları-Global-BV2-23-29 May.csv' # For display

df_bv2_cleaned = load_data(cleaned_bv2_file)
df_bv5_cleaned = load_data(cleaned_bv5_file)
df_bv5_may23_cleaned = load_data(cleaned_bv5_may23_file) # Load new BV5 data
df_tt_bv2_may23_cleaned = load_data(cleaned_tt_bv2_may23_file) # Load new TT BV2 data

# # ---- Start Temporary Debugging for Streamlit Cloud ----
# st.sidebar.subheader("Debug: /mount/src/ads_analysis/data/ contents")
# try:
#     data_dir_path_on_cloud = "/mount/src/ads_analysis/data/"
#     if os.path.exists(data_dir_path_on_cloud):
#         cloud_data_files = os.listdir(data_dir_path_on_cloud)
#         st.sidebar.write(f"Files in {data_dir_path_on_cloud}:")
#         for f_name in cloud_data_files:
#             st.sidebar.write(f"- {f_name}")
#     else:
#         st.sidebar.warning(f"Debug: Path {data_dir_path_on_cloud} does NOT exist on Streamlit Cloud.")
# except Exception as e_debug:
#     st.sidebar.error(f"Debug: Error listing {data_dir_path_on_cloud}: {e_debug}")
# # ---- End Temporary Debugging ----

st.title("Facebook Reklam Performans Analizi Dashboard")

tab1_title = "BV2 Analizi (10-22 Mayıs)"
tab2_title = "BV5 Analizi (10-22 Mayıs)"
tab3_title = "BV5 Analizi (23-29 Mayıs)"
tab4_title = "TT BV2 Analizi (23-29 Mayıs)"

tab1, tab2, tab3, tab4 = st.tabs([tab1_title, tab2_title, tab3_title, tab4_title])

# Define these globally or ensure they are available/passed to tabs
spending_threshold = 30 # Consistent threshold
cols_to_display_countries = ['Country', 'Total Spent (USD)', 'Total Reach', 'Total Link Clicks', 'Total Results', 'CTR (%)', 'CPC (USD)', 'CPM (USD)', 'Avg. Cost per Result (USD)']
style_format_countries = column_formatters() # Use the global formatter

with tab1:
    st.header(tab1_title)
    if df_bv2_cleaned is not None:
        original_rows = get_original_row_count(original_bv2_file_name)
        # The existing detailed data cleaning markdown for tab1 can remain if it's specific
        st.subheader(f"Veri Temizleme Süreci ({original_bv2_file_name})")
        st.markdown(f"""
        Analizler için kullanılan orijinal `{original_bv2_file_name}` veri seti üzerinde bir temizlik işlemi uygulanmıştır:
        - **`Country` (Ülke) sütununda değeri olmayan satırlar veri setinden çıkarıldı.** Bu işlem, hem Facebook'un otomatik oluşturduğu olası bir genel toplam satırını hem de ülke bilgisi eksik olan diğer münferit satırları kapsamaktadır.
        - Orijinal veri setinde **{original_rows:,} satır** bulunuyordu.
        - Temizlik işlemi sonucunda **{original_rows - len(df_bv2_cleaned):,} satır çıkarılarak** veri seti **{len(df_bv2_cleaned):,} satıra** düşürüldü.
        - Bu temizlenmiş ve analize hazır veri, `{cleaned_bv2_file}` dosyasına kaydedilmiştir.
        Bu ön işleme adımı, analizlerimizin yalnızca geçerli ve tanımlı ülke verilerine dayanmasını sağlayarak daha doğru ve güvenilir sonuçlar elde etmemize olanak tanımıştır.
        """)
        st.divider()

        st.subheader(f"Detaylı KPI Analizleri ({tab1_title})")
        df_bv2_processed = calculate_kpis_for_display(df_bv2_cleaned.copy())
        country_summary_kpis_tab1 = prepare_country_kpis(df_bv2_processed, dataset_name=tab1_title)

        st.markdown(f"#### Harcaması {spending_threshold} USD Üzerinde Olan Ülkeler ve KPI'ları")
        top_countries_df_tab1 = country_summary_kpis_tab1[country_summary_kpis_tab1['Total Spent (USD)'] > spending_threshold]
        if not top_countries_df_tab1.empty:
            st.dataframe(top_countries_df_tab1[cols_to_display_countries].style.format(style_format_countries), use_container_width=True)
        else:
            st.info(f"Belirtilen harcama ({spending_threshold} USD) üzerinde ülke bulunamadı ({tab1_title}).")

        st.markdown("#### Türkiye (TR) ve Azerbaycan (AZ) için Özel KPI Değerleri")
        tr_az_countries_df_tab1 = country_summary_kpis_tab1[country_summary_kpis_tab1['Country'].isin(['Turkey', 'Azerbaijan'])]
        if not tr_az_countries_df_tab1.empty:
            st.dataframe(tr_az_countries_df_tab1[cols_to_display_countries].style.format(style_format_countries), use_container_width=True)
        else:
            st.info(f"Veri setinde Türkiye (TR) veya Azerbaycan (AZ) için tanımlı harcama bilgisi bulunamadı ({tab1_title}).")

        st.markdown("#### Global Ortalamalar (Türkiye ve Azerbaycan Hariç)")
        df_global_avg_source_tab1 = df_bv2_processed[~df_bv2_processed['Country'].isin(['TR', 'AZ'])]
        if not df_global_avg_source_tab1.empty:
            global_total_spent = df_global_avg_source_tab1['Amount spent (USD)'].sum()
            global_total_impressions = df_global_avg_source_tab1['Impressions'].sum()
            global_total_link_clicks = df_global_avg_source_tab1['Link clicks'].sum()
            global_total_reach = df_global_avg_source_tab1['Reach'].sum()
            global_total_results = df_global_avg_source_tab1['Results'].sum()
            global_avg_ctr = (global_total_link_clicks / global_total_impressions) * 100 if global_total_impressions > 0 else 0
            global_avg_cpc = global_total_spent / global_total_link_clicks if global_total_link_clicks > 0 else 0
            global_avg_cpm = (global_total_spent / global_total_impressions) * 1000 if global_total_impressions > 0 else 0
            global_avg_cost_per_result = (global_total_spent / global_total_results) if global_total_results > 0 else 0
            global_avg_data = {
                'Metrik': [f'Global Ortalama (TR ve AZ Hariç) - {tab1_title}'], 'Toplam Harcama (USD)': [global_total_spent],
                'Toplam Reach': [global_total_reach], 'Toplam Gösterim (Impressions)': [global_total_impressions],
                'Toplam Link Tıklaması': [global_total_link_clicks], 'Toplam Sonuç (Results)': [global_total_results],
                'Ortalama CTR (%)': [global_avg_ctr], 'Ortalama CPC (USD)': [global_avg_cpc],
                'Ortalama CPM (USD)': [global_avg_cpm], 'Ortalama Sonuç Başına Maliyet (USD)': [global_avg_cost_per_result]
            }
            global_avg_display_df_tab1 = pd.DataFrame(global_avg_data)
            st.dataframe(global_avg_display_df_tab1.style.format(column_formatters()), use_container_width=True)
        else:
            st.info(f"TR ve AZ dışındaki ülkeler için global ortalama hesaplanacak veri bulunamadı ({tab1_title}).")
        
        display_ad_set_analysis(df_bv2_processed, analyze_ad_sets, tab1_title, top_n_ad_sets=10)
    else:
        st.error(f"`{cleaned_bv2_file}` dosyası yüklenemediği için {tab1_title} analizleri gösterilemiyor.")

with tab2: # BV5 (10-22 Mayıs)
    st.header(tab2_title)
    if df_bv5_cleaned is not None:
        original_rows = get_original_row_count(original_bv5_file_name)
        display_cleaning_info(original_rows, len(df_bv5_cleaned), original_bv5_file_name) # Use original_bv5_file_name for dataset_name
        st.subheader(f"Detaylı KPI Analizleri ({tab2_title})")
        df_bv5_processed = calculate_kpis_for_display(df_bv5_cleaned.copy())
        country_summary_kpis_tab2 = prepare_country_kpis(df_bv5_processed, dataset_name=tab2_title)

        st.markdown(f"#### Harcaması {spending_threshold} USD Üzerinde Olan Ülkeler ve KPI'ları")
        top_countries_df_tab2 = country_summary_kpis_tab2[country_summary_kpis_tab2['Total Spent (USD)'] > spending_threshold]
        if not top_countries_df_tab2.empty:
            st.dataframe(top_countries_df_tab2[cols_to_display_countries].style.format(style_format_countries), use_container_width=True)
        else:
            st.info(f"Belirtilen harcama ({spending_threshold} USD) üzerinde ülke bulunamadı ({tab2_title}).")

        st.markdown("#### Türkiye (TR) ve Azerbaycan (AZ) için Özel KPI Değerleri")
        tr_az_countries_df_tab2 = country_summary_kpis_tab2[country_summary_kpis_tab2['Country'].isin(['Turkey', 'Azerbaijan'])]
        if not tr_az_countries_df_tab2.empty:
            st.dataframe(tr_az_countries_df_tab2[cols_to_display_countries].style.format(style_format_countries), use_container_width=True)
        else:
            st.info(f"Veri setinde Türkiye (TR) veya Azerbaycan (AZ) için tanımlı harcama bilgisi bulunamadı ({tab2_title}).")

        st.markdown("#### Global Ortalamalar (Türkiye ve Azerbaycan Hariç)")
        df_global_avg_source_tab2 = df_bv5_processed[~df_bv5_processed['Country'].isin(['TR', 'AZ'])]
        if not df_global_avg_source_tab2.empty:
            global_total_spent = df_global_avg_source_tab2['Amount spent (USD)'].sum()
            global_total_impressions = df_global_avg_source_tab2['Impressions'].sum()
            global_total_link_clicks = df_global_avg_source_tab2['Link clicks'].sum()
            global_total_reach = df_global_avg_source_tab2['Reach'].sum()
            global_total_results = df_global_avg_source_tab2['Results'].sum()
            global_avg_ctr = (global_total_link_clicks / global_total_impressions) * 100 if global_total_impressions > 0 else 0
            global_avg_cpc = global_total_spent / global_total_link_clicks if global_total_link_clicks > 0 else 0
            global_avg_cpm = (global_total_spent / global_total_impressions) * 1000 if global_total_impressions > 0 else 0
            global_avg_cost_per_result = (global_total_spent / global_total_results) if global_total_results > 0 else 0
            global_avg_data = {
                'Metrik': [f'Global Ortalama (TR ve AZ Hariç) - {tab2_title}'], 'Toplam Harcama (USD)': [global_total_spent],
                'Toplam Reach': [global_total_reach], 'Toplam Gösterim (Impressions)': [global_total_impressions],
                'Toplam Link Tıklaması': [global_total_link_clicks], 'Toplam Sonuç (Results)': [global_total_results],
                'Ortalama CTR (%)': [global_avg_ctr], 'Ortalama CPC (USD)': [global_avg_cpc],
                'Ortalama CPM (USD)': [global_avg_cpm], 'Ortalama Sonuç Başına Maliyet (USD)': [global_avg_cost_per_result]
            }
            global_avg_display_df_tab2 = pd.DataFrame(global_avg_data)
            st.dataframe(global_avg_display_df_tab2.style.format(column_formatters()), use_container_width=True)
        else:
            st.info(f"TR ve AZ dışındaki ülkeler için global ortalama hesaplanacak veri bulunamadı ({tab2_title}).")

        top_n_ad_sets = 10 
        df_bv5_for_ad_set_display = df_bv5_processed.copy()
        # clean_bv5_global.csv is expected to have 'Ad Set Name' directly
        display_ad_set_analysis(df_bv5_for_ad_set_display, analyze_ad_sets_bv5, tab2_title, top_n_ad_sets=top_n_ad_sets)
    else:
        st.error(f"`{cleaned_bv5_file}` dosyası yüklenemediği için {tab2_title} analizleri gösterilemiyor.")

with tab3: # BV5 (23-29 Mayıs)
    st.header(tab3_title)
    if df_bv5_may23_cleaned is not None:
        original_rows = get_original_row_count(original_bv5_may23_file_name)
        display_cleaning_info(original_rows, len(df_bv5_may23_cleaned), original_bv5_may23_file_name)
        st.subheader(f"Detaylı KPI Analizleri ({tab3_title})")
        df_bv5_may23_processed = calculate_kpis_for_display(df_bv5_may23_cleaned.copy())
        country_summary_kpis_tab3 = prepare_country_kpis(df_bv5_may23_processed, dataset_name=tab3_title)

        st.markdown(f"#### Harcaması {spending_threshold} USD Üzerinde Olan Ülkeler ve KPI'ları")
        top_countries_df_tab3 = country_summary_kpis_tab3[country_summary_kpis_tab3['Total Spent (USD)'] > spending_threshold]
        if not top_countries_df_tab3.empty:
            st.dataframe(top_countries_df_tab3[cols_to_display_countries].style.format(style_format_countries), use_container_width=True)
        else:
            st.info(f"Belirtilen harcama ({spending_threshold} USD) üzerinde ülke bulunamadı ({tab3_title}).")

        st.markdown("#### Türkiye (TR) ve Azerbaycan (AZ) için Özel KPI Değerleri")
        tr_az_countries_df_tab3 = country_summary_kpis_tab3[country_summary_kpis_tab3['Country'].isin(['Turkey', 'Azerbayjan'])]
        if not tr_az_countries_df_tab3.empty:
            st.dataframe(tr_az_countries_df_tab3[cols_to_display_countries].style.format(style_format_countries), use_container_width=True)
        else:
            st.info(f"Veri setinde Türkiye (TR) veya Azerbaycan (AZ) için tanımlı harcama bilgisi bulunamadı ({tab3_title}).")

        st.markdown("#### Global Ortalamalar (Türkiye ve Azerbaycan Hariç)")
        df_global_avg_source_tab3 = df_bv5_may23_processed[~df_bv5_may23_processed['Country'].isin(['TR', 'AZ'])]
        if not df_global_avg_source_tab3.empty:
            global_total_spent = df_global_avg_source_tab3['Amount spent (USD)'].sum()
            global_total_impressions = df_global_avg_source_tab3['Impressions'].sum()
            global_total_link_clicks = df_global_avg_source_tab3['Link clicks'].sum()
            global_total_reach = df_global_avg_source_tab3['Reach'].sum()
            global_total_results = df_global_avg_source_tab3['Results'].sum()
            global_avg_ctr = (global_total_link_clicks / global_total_impressions) * 100 if global_total_impressions > 0 else 0
            global_avg_cpc = global_total_spent / global_total_link_clicks if global_total_link_clicks > 0 else 0
            global_avg_cpm = (global_total_spent / global_total_impressions) * 1000 if global_total_impressions > 0 else 0
            global_avg_cost_per_result = (global_total_spent / global_total_results) if global_total_results > 0 else 0
            global_avg_data = {
                'Metrik': [f'Global Ortalama (TR ve AZ Hariç) - {tab3_title}'], 'Toplam Harcama (USD)': [global_total_spent],
                'Toplam Reach': [global_total_reach], 'Toplam Gösterim (Impressions)': [global_total_impressions],
                'Toplam Link Tıklaması': [global_total_link_clicks], 'Toplam Sonuç (Results)': [global_total_results],
                'Ortalama CTR (%)': [global_avg_ctr], 'Ortalama CPC (USD)': [global_avg_cpc],
                'Ortalama CPM (USD)': [global_avg_cpm], 'Ortalama Sonuç Başına Maliyet (USD)': [global_avg_cost_per_result]
            }
            global_avg_display_df_tab3 = pd.DataFrame(global_avg_data)
            st.dataframe(global_avg_display_df_tab3.style.format(column_formatters()), use_container_width=True)
        else:
            st.info(f"TR ve AZ dışındaki ülkeler için global ortalama hesaplanacak veri bulunamadı ({tab3_title}).")
        
        df_bv5_may23_for_ad_set_display = df_bv5_may23_processed.copy()
        if 'Campaign name' in df_bv5_may23_for_ad_set_display.columns:
            df_bv5_may23_for_ad_set_display.rename(columns={'Campaign name': 'Ad Set Name'}, inplace=True)
        elif 'Ad Set Name' not in df_bv5_may23_for_ad_set_display.columns: 
             df_bv5_may23_for_ad_set_display['Ad Set Name'] = "Unknown Ad Set"
        display_ad_set_analysis(df_bv5_may23_for_ad_set_display, analyze_ad_sets_bv5_may23_specific, tab3_title)
    else:
        st.error(f"`{cleaned_bv5_may23_file}` dosyası yüklenemediği için {tab3_title} analizleri gösterilemiyor.")

with tab4: # TT BV2 (23-29 Mayıs)
    st.header(tab4_title)
    if df_tt_bv2_may23_cleaned is not None:
        original_rows = get_original_row_count(original_tt_bv2_may23_file_name)
        display_cleaning_info(original_rows, len(df_tt_bv2_may23_cleaned), original_tt_bv2_may23_file_name)
        st.subheader(f"Detaylı KPI Analizleri ({tab4_title})")
        df_tt_bv2_may23_processed = calculate_kpis_for_display(df_tt_bv2_may23_cleaned.copy())
        country_summary_kpis_tab4 = prepare_country_kpis(df_tt_bv2_may23_processed, dataset_name=tab4_title)

        st.markdown(f"#### Harcaması {spending_threshold} USD Üzerinde Olan Ülkeler ve KPI'ları")
        top_countries_df_tab4 = country_summary_kpis_tab4[country_summary_kpis_tab4['Total Spent (USD)'] > spending_threshold]
        if not top_countries_df_tab4.empty:
            st.dataframe(top_countries_df_tab4[cols_to_display_countries].style.format(style_format_countries), use_container_width=True)
        else:
            st.info(f"Belirtilen harcama ({spending_threshold} USD) üzerinde ülke bulunamadı ({tab4_title}).")

        st.markdown("#### Türkiye (TR) ve Azerbaycan (AZ) için Özel KPI Değerleri")
        tr_az_countries_df_tab4 = country_summary_kpis_tab4[country_summary_kpis_tab4['Country'].isin(['Turkey', 'Azerbaijan'])]
        if not tr_az_countries_df_tab4.empty:
            st.dataframe(tr_az_countries_df_tab4[cols_to_display_countries].style.format(style_format_countries), use_container_width=True)
        else:
            st.info(f"Veri setinde Türkiye (TR) veya Azerbaycan (AZ) için tanımlı harcama bilgisi bulunamadı ({tab4_title}).")

        st.markdown("#### Global Ortalamalar (Türkiye ve Azerbaycan Hariç)")
        df_global_avg_source_tab4 = df_tt_bv2_may23_processed[~df_tt_bv2_may23_processed['Country'].isin(['TR', 'AZ'])]
        if not df_global_avg_source_tab4.empty:
            global_total_spent = df_global_avg_source_tab4['Amount spent (USD)'].sum()
            global_total_impressions = df_global_avg_source_tab4['Impressions'].sum()
            global_total_link_clicks = df_global_avg_source_tab4['Link clicks'].sum()
            global_total_reach = df_global_avg_source_tab4['Reach'].sum()
            global_total_results = df_global_avg_source_tab4['Results'].sum()
            global_avg_ctr = (global_total_link_clicks / global_total_impressions) * 100 if global_total_impressions > 0 else 0
            global_avg_cpc = global_total_spent / global_total_link_clicks if global_total_link_clicks > 0 else 0
            global_avg_cpm = (global_total_spent / global_total_impressions) * 1000 if global_total_impressions > 0 else 0
            global_avg_cost_per_result = (global_total_spent / global_total_results) if global_total_results > 0 else 0
            global_avg_data = {
                'Metrik': [f'Global Ortalama (TR ve AZ Hariç) - {tab4_title}'], 'Toplam Harcama (USD)': [global_total_spent],
                'Toplam Reach': [global_total_reach], 'Toplam Gösterim (Impressions)': [global_total_impressions],
                'Toplam Link Tıklaması': [global_total_link_clicks], 'Toplam Sonuç (Results)': [global_total_results],
                'Ortalama CTR (%)': [global_avg_ctr], 'Ortalama CPC (USD)': [global_avg_cpc],
                'Ortalama CPM (USD)': [global_avg_cpm], 'Ortalama Sonuç Başına Maliyet (USD)': [global_avg_cost_per_result]
            }
            global_avg_display_df_tab4 = pd.DataFrame(global_avg_data)
            st.dataframe(global_avg_display_df_tab4.style.format(column_formatters()), use_container_width=True)
        else:
            st.info(f"TR ve AZ dışındaki ülkeler için global ortalama hesaplanacak veri bulunamadı ({tab4_title}).")

        df_tt_bv2_for_ad_set_display = df_tt_bv2_may23_processed.copy()
        if 'Campaign name' in df_tt_bv2_for_ad_set_display.columns:
            df_tt_bv2_for_ad_set_display.rename(columns={'Campaign name': 'Ad Set Name'}, inplace=True)
        elif 'Ad Set Name' not in df_tt_bv2_for_ad_set_display.columns:
             df_tt_bv2_for_ad_set_display['Ad Set Name'] = "Unknown Ad Set"
        display_ad_set_analysis(df_tt_bv2_for_ad_set_display, analyze_ad_sets_tt_bv2_may23_specific, tab4_title)
    else:
        st.error(f"`{cleaned_tt_bv2_may23_file}` dosyası yüklenemediği için {tab4_title} analizleri gösterilemiyor.")

st.sidebar.header("Ayarlar")
