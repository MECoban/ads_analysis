import streamlit as st
import pandas as pd
import numpy as np
import os

# Import analyzer functions - we will likely need to choose ONE and adapt its use,
# or create a new generic one for combined data.
# For now, let's plan to use an aliased version of one of the existing 'analyze_ad_sets'
# that expects 'Ad Set Name' after we prepare the 'Universal_Campaign_ID'.
from global_analyzer import analyze_ad_sets as generic_analyze_ad_sets
# We might not need the other specific analyzers if we generalize properly.

st.set_page_config(layout="wide")

country_code_to_name_map = {
    "TR": "Turkey", "AZ": "Azerbaijan", "US": "United States", "DE": "Germany",
    "GB": "United Kingdom", "UZ": "Uzbekistan", "CA": "Canada", "AU": "Australia",
    "FR": "France", "NL": "Netherlands", "AE": "United Arab Emirates",
}

# --- Global Helper Functions (get_original_row_count, display_cleaning_info, column_formatters, prepare_country_kpis, calculate_kpis_for_display, display_ad_set_analysis, load_data) ---
# These functions will largely remain the same, but their usage context will change.
# display_ad_set_analysis will need to be called with the correct UNIVERSAL_ID_COLUMN after renaming.
# get_original_row_count and display_cleaning_info will now be less relevant as we use pre-combined files for main display.

UNIVERSAL_ID_COLUMN = 'Universal_Campaign_ID' # Standardized column name

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        # print(f"Loaded {file_path} with columns: {df.columns.tolist()}") # Optional debug
        return df
    except FileNotFoundError:
        st.error(f"Hata: '{file_path}' dosyası bulunamadı.")
        return None
    except Exception as e:
        st.error(f"'{file_path}' okunurken bir hata oluştu: {e}")
        return None

# --- (Copying existing helper functions here for completeness in this edit block) ---
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

def column_formatters(): # This can remain global
    return {
        "Total Spent (USD)": "${:,.2f}", "Total Reach": "{:,.0f}", "Total Impressions": "{:,.0f}",
        "Total Link Clicks": "{:,.0f}", "Total Results": "{:,.0f}", "CTR (%)": "{:.2f}%",
        "CPC (USD)": "${:,.2f}", "CPM (USD)": "${:,.2f}", "Avg. Cost per Result (USD)": "${:,.2f}",
        "Toplam Harcama (USD)": "${:,.2f}", "Toplam Reach": "{:,.0f}", "Toplam Gösterim (Impressions)": "{:,.0f}",
        "Toplam Link Tıklaması": "{:,.0f}", "Toplam Sonuç (Results)": "{:,.0f}",
        "Ortalama CTR (%)": "{:.2f}%", "Ortalama CPC (USD)": "${:,.2f}",
        "Ortalama CPM (USD)": "${:,.2f}", "Ortalama Sonuç Başına Maliyet (USD)": "${:,.2f}",
        # Sales funnel columns
        "Randevu": "{:,.0f}", "Katılım": "{:,.0f}", "Satış": "{:,.0f}",
        "Rndv-Ktlm (%)": "{:.2f}%", "Ktlm-Sts (%)": "{:.2f}%", "Rndv-Sts (%)": "{:.2f}%"
    }

def prepare_country_kpis(df_cleaned, dataset_name="Dataset"):
    if df_cleaned is None or df_cleaned.empty:
        st.warning(f"Cannot prepare country KPIs for {dataset_name}: Input data is empty or None.")
        return pd.DataFrame()
    df_processed = calculate_kpis_for_display(df_cleaned.copy())
    country_summary_agg = df_processed.groupby('Country').agg(
        total_spent=('Amount spent (USD)', 'sum'), total_impressions=('Impressions', 'sum'),
        total_link_clicks=('Link clicks', 'sum'), total_reach=('Reach', 'sum'),
        total_results=('Results', 'sum')).reset_index()
    country_summary_for_kpis = country_summary_agg.rename(columns={
        'total_spent': 'Amount spent (USD)', 'total_impressions': 'Impressions',
        'total_link_clicks': 'Link clicks', 'total_reach': 'Reach', 'total_results': 'Results'})
    country_summary_kpis = calculate_kpis_for_display(country_summary_for_kpis)
    country_summary_kpis['Avg. Cost per Result (USD)'] = np.where(
        country_summary_kpis['Results'] > 0,
        country_summary_kpis['Amount spent (USD)'] / country_summary_kpis['Results'], 0)
    country_summary_kpis = country_summary_kpis.rename(columns={
        'Amount spent (USD)': 'Total Spent (USD)', 'Impressions': 'Total Impressions',
        'Link clicks': 'Total Link Clicks', 'Reach': 'Total Reach', 'Results': 'Total Results'
    }).sort_values(by='Total Spent (USD)', ascending=False)
    country_summary_kpis_display = country_summary_kpis.copy()
    country_summary_kpis_display['Country'] = country_summary_kpis_display['Country'].map(country_code_to_name_map).fillna(country_summary_kpis_display['Country'])
    return country_summary_kpis_display

def display_ad_set_analysis_modified(df_input, analyze_func, id_column_name, dataset_label, top_n=10):
    if df_input is None or df_input.empty or id_column_name not in df_input.columns:
        st.warning(f"`{id_column_name}` sütunu {dataset_label} veri setinde bulunamadı veya veri boş. Analiz yapılamıyor.")
        return
    df_processed_for_analyzer = df_input.copy()
    if id_column_name != 'Ad Set Name': # Analyzer expects 'Ad Set Name'
        df_processed_for_analyzer.rename(columns={id_column_name: 'Ad Set Name'}, inplace=True)
    
    tr_name = country_code_to_name_map.get('TR', 'TR')
    az_name = country_code_to_name_map.get('AZ', 'AZ')
    cols_to_display = ['Ad Set Name', 'Total Spent (USD)', 'Total Reach', 'Total Link Clicks', 'Total Results', 'CTR (%)', 'CPC (USD)', 'CPM (USD)', 'Avg. Cost per Result (USD)']
    style_formats = column_formatters()

    st.header(f"Kampanya/Reklam Seti Bazlı KPI Analizleri ({dataset_label})")
    def _display_tables(results_df, spent_df, label_suffix):
        full_label = f"{label_suffix} ({dataset_label})"
        st.markdown(f"##### En Çok Sonuç Getiren İlk {top_n} Kampanya/Reklam Seti ({full_label})")
        if results_df is not None and not results_df.empty: st.dataframe(results_df[cols_to_display].style.format(style_formats), use_container_width=True)
        else: st.info(f"Sonuçlara göre sıralanacak kampanya/reklam seti bulunamadı ({full_label}).")
        st.markdown(f"##### En Çok Harcama Yapan İlk {top_n} Kampanya/Reklam Seti ({full_label})")
        if spent_df is not None and not spent_df.empty: st.dataframe(spent_df[cols_to_display].style.format(style_formats), use_container_width=True)
        else: st.info(f"Harcamalara göre sıralanacak kampanya/reklam seti bulunamadı ({full_label}).")
        st.caption(f"Not: Yukarıdaki analizler {full_label} için geçerlidir."); st.divider()

    st.markdown(f"#### {tr_name} Performansı")
    tr_results, tr_spent = analyze_func(df_processed_for_analyzer, target_countries=['TR'], filter_type='include', top_n=top_n)
    _display_tables(tr_results, tr_spent, tr_name)
    st.markdown(f"#### {az_name} Performansı")
    az_results, az_spent = analyze_func(df_processed_for_analyzer, target_countries=['AZ'], filter_type='include', top_n=top_n)
    _display_tables(az_results, az_spent, az_name)
    global_label = f"Global ({tr_name} ve {az_name} Hariç)"
    st.markdown(f"#### {global_label} Performansı")
    g_results, g_spent = analyze_func(df_processed_for_analyzer, target_countries=['TR', 'AZ'], filter_type='exclude', top_n=top_n)
    _display_tables(g_results, g_spent, global_label)

def display_regional_sales_kpis(period_label, period_ad_df_processed, period_sales_df, country_code_map):
    st.header(f"Bölgesel Satış KPI'ları ({period_label})")

    regions_to_display = {
        'Turkey': ['TR'],
        'Azerbaijan': ['AZ'],
        'Global (TR ve AZ Hariç)': 'exclude_tr_az' # Special case
    }

    kpi_data_list = []

    for display_name, country_codes_or_flag in regions_to_display.items():
        # Initialize metrics
        total_spent, total_reach, total_link_clicks, total_impressions = 0, 0, 0, 0
        randevu_sayisi, satis_sayisi = 0, 0

        # --- Aggregate Ad Data ---
        if country_codes_or_flag == 'exclude_tr_az':
            region_ad_data = period_ad_df_processed[~period_ad_df_processed['Country'].isin(['TR', 'AZ'])]
        else:
            region_ad_data = period_ad_df_processed[period_ad_df_processed['Country'].isin(country_codes_or_flag)]
        
        if not region_ad_data.empty:
            total_spent = region_ad_data['Amount spent (USD)'].sum()
            total_reach = region_ad_data['Reach'].sum()
            total_link_clicks = region_ad_data['Link clicks'].sum()
            total_impressions = region_ad_data['Impressions'].sum()

        ctr = (total_link_clicks / total_impressions) * 100 if total_impressions > 0 else 0
        cpc = total_spent / total_link_clicks if total_link_clicks > 0 else 0
        cpm = (total_spent / total_impressions) * 1000 if total_impressions > 0 else 0

        # --- Get Sales Data ---
        # Map display_name to region name in sales_df ('Turkey' -> 'TR', 'Azerbaijan' -> 'AZE', 'Global (TR ve AZ Hariç)' -> 'Global')
        sales_region_name = display_name
        if display_name == 'Turkey': sales_region_name = 'TR'
        elif display_name == 'Azerbaijan': sales_region_name = 'AZE'
        elif display_name == 'Global (TR ve AZ Hariç)': sales_region_name = 'Global'
        
        region_sales_data = period_sales_df[period_sales_df['Region'] == sales_region_name]

        if not region_sales_data.empty:
            randevu_sayisi = region_sales_data['Randevu'].sum() # Sum if multiple rows (should be 1)
            satis_sayisi = region_sales_data['Satış'].sum()   # Sum if multiple rows

        # --- Calculate Combined KPIs ---
        randevu_maliyeti = total_spent / randevu_sayisi if randevu_sayisi > 0 else 0
        cpa = total_spent / satis_sayisi if satis_sayisi > 0 else 0

        kpi_data_list.append({
            'Bölge': display_name,
            'Total Spent (USD)': total_spent,
            'Total Reach': total_reach,
            'Total Link Clicks': total_link_clicks,
            'CTR (%)': ctr,
            'CPC (USD)': cpc,
            'CPM (USD)': cpm,
            'Randevu Sayısı': randevu_sayisi,
            'Randevu Maliyeti (USD)': randevu_maliyeti,
            'Satış Sayısı': satis_sayisi,
            'CPA (USD)': cpa
        })

    if kpi_data_list:
        kpi_df = pd.DataFrame(kpi_data_list)
        cols_ordered = ['Bölge', 'Total Spent (USD)', 'Total Reach', 'Total Link Clicks', 'CTR (%)', 'CPC (USD)', 'CPM (USD)', 'Randevu Sayısı', 'Randevu Maliyeti (USD)', 'Satış Sayısı', 'CPA (USD)']
        # Ensure all columns in cols_ordered are present in kpi_df, add if missing (e.g. if all values were 0)
        for col in cols_ordered:
            if col not in kpi_df.columns:
                kpi_df[col] = 0 # Or np.nan depending on desired display for missing data
        
        # Get a new formatter dict that includes sales KPI formats
        extended_formatters = column_formatters() # Assuming column_formatters is updated or new ones are added
        extended_formatters.update({
            'Randevu Sayısı': '{:,.0f}',
            'Randevu Maliyeti (USD)': '${:,.2f}',
            'Satış Sayısı': '{:,.0f}',
            'CPA (USD)': '${:,.2f}'
        })
        st.dataframe(kpi_df[cols_ordered].style.format(extended_formatters), use_container_width=True)
    else:
        st.info("Bölgesel satış KPI'ları için veri bulunamadı.")
    st.divider()

# Paths to the NEW combined data files
combined_file_p1 = 'data/combined_period1_10_22_may.csv'
combined_file_p2 = 'data/combined_period2_23_29_may.csv'
sales_file = 'data/sales.csv'

# Load combined datasets
df_p1 = load_data(combined_file_p1)
df_p2 = load_data(combined_file_p2)
df_sales = load_data(sales_file)

st.title("Reklam ve Satış Performans Analizi Dashboard")

# Define common display elements
spending_threshold = 30
cols_to_display_countries = ['Country', 'Total Spent (USD)', 'Total Reach', 'Total Link Clicks', 'Total Results', 'CTR (%)', 'CPC (USD)', 'CPM (USD)', 'Avg. Cost per Result (USD)']
# style_format_countries is already available from column_formatters()

period1_title = "Dönem Analizi (10-22 Mayıs)"
period2_title = "Dönem Analizi (23-29 Mayıs)"

tab_p1, tab_p2 = st.tabs([period1_title, period2_title])

with tab_p1:
    st.header(period1_title)
    if df_p1 is not None:
        st.subheader(f"Veri Kaynağı: `{combined_file_p1}`")
        df_p1_processed = calculate_kpis_for_display(df_p1.copy())
        country_summary_kpis_p1 = prepare_country_kpis(df_p1_processed, dataset_name=period1_title)

        # --- Country KPIs for Period 1 ---
        st.subheader("Ülke Bazlı Genel KPI'lar")
        st.markdown(f"##### Harcaması {spending_threshold} USD Üzerinde Olan Ülkeler")
        top_countries_df_p1 = country_summary_kpis_p1[country_summary_kpis_p1['Total Spent (USD)'] > spending_threshold]
        if not top_countries_df_p1.empty: st.dataframe(top_countries_df_p1[cols_to_display_countries].style.format(column_formatters()), use_container_width=True)
        else: st.info(f"Belirtilen harcama üzerinde ülke bulunamadı.")
        st.markdown("##### Türkiye (TR) ve Azerbaycan (AZ) için Özel KPI'lar")
        tr_az_df_p1 = country_summary_kpis_p1[country_summary_kpis_p1['Country'].isin(['Turkey', 'Azerbaijan'])]
        if not tr_az_df_p1.empty: st.dataframe(tr_az_df_p1[cols_to_display_countries].style.format(column_formatters()), use_container_width=True)
        else: st.info("TR veya AZ için veri bulunamadı.")
        st.markdown("##### Global Ortalamalar (TR ve AZ Hariç)")
        df_global_avg_src_p1 = df_p1_processed[~df_p1_processed['Country'].isin(['TR', 'AZ'])]
        if not df_global_avg_src_p1.empty:
            global_total_spent_p1 = df_global_avg_src_p1['Amount spent (USD)'].sum()
            global_total_impressions_p1 = df_global_avg_src_p1['Impressions'].sum()
            global_total_link_clicks_p1 = df_global_avg_src_p1['Link clicks'].sum()
            global_total_reach_p1 = df_global_avg_src_p1['Reach'].sum()
            global_total_results_p1 = df_global_avg_src_p1['Results'].sum()
            global_avg_ctr_p1 = (global_total_link_clicks_p1 / global_total_impressions_p1) * 100 if global_total_impressions_p1 > 0 else 0
            global_avg_cpc_p1 = global_total_spent_p1 / global_total_link_clicks_p1 if global_total_link_clicks_p1 > 0 else 0
            global_avg_cpm_p1 = (global_total_spent_p1 / global_total_impressions_p1) * 1000 if global_total_impressions_p1 > 0 else 0
            global_avg_cost_per_result_p1 = (global_total_spent_p1 / global_total_results_p1) if global_total_results_p1 > 0 else 0
            global_avg_data_p1 = {
                'Metrik': [f'Global Ortalama (TR ve AZ Hariç) - {period1_title}'], 'Toplam Harcama (USD)': [global_total_spent_p1],
                'Toplam Reach': [global_total_reach_p1], 'Toplam Gösterim (Impressions)': [global_total_impressions_p1],
                'Toplam Link Tıklaması': [global_total_link_clicks_p1], 'Toplam Sonuç (Results)': [global_total_results_p1],
                'Ortalama CTR (%)': [global_avg_ctr_p1], 'Ortalama CPC (USD)': [global_avg_cpc_p1],
                'Ortalama CPM (USD)': [global_avg_cpm_p1], 'Ortalama Sonuç Başına Maliyet (USD)': [global_avg_cost_per_result_p1]}
            global_avg_display_df_p1 = pd.DataFrame(global_avg_data_p1)
            st.dataframe(global_avg_display_df_p1.style.format(column_formatters()), use_container_width=True)
        else: st.info(f"Global ortalama için TR/AZ dışında veri bulunamadı ({period1_title}).")
        st.divider()
        # --- Campaign/Ad Set Analysis for Period 1 ---
        display_ad_set_analysis_modified(df_p1_processed, generic_analyze_ad_sets, UNIVERSAL_ID_COLUMN, period1_title)
        st.divider()
        # --- Sales Funnel for Period 1 (22 Mayıs) ---
        if df_sales is not None:
            sales_p1_data = df_sales[df_sales['Period'] == '22 Mayıs']
            display_regional_sales_kpis("22 Mayıs", df_p1_processed, sales_p1_data, country_code_to_name_map)
    else: st.error(f"`{combined_file_p1}` yüklenemedi.")

with tab_p2:
    st.header(period2_title)
    if df_p2 is not None:
        st.subheader(f"Veri Kaynağı: `{combined_file_p2}`")
        df_p2_processed = calculate_kpis_for_display(df_p2.copy())
        country_summary_kpis_p2 = prepare_country_kpis(df_p2_processed, dataset_name=period2_title)
        # --- Country KPIs for Period 2 (similar to Period 1) ---
        st.subheader("Ülke Bazlı Genel KPI'lar")
        st.markdown(f"##### Harcaması {spending_threshold} USD Üzerinde Olan Ülkeler")
        top_countries_df_p2 = country_summary_kpis_p2[country_summary_kpis_p2['Total Spent (USD)'] > spending_threshold]
        if not top_countries_df_p2.empty: st.dataframe(top_countries_df_p2[cols_to_display_countries].style.format(column_formatters()), use_container_width=True)
        else: st.info(f"Belirtilen harcama üzerinde ülke bulunamadı.")
        st.markdown("##### Türkiye (TR) ve Azerbaycan (AZ) için Özel KPI'lar")
        tr_az_df_p2 = country_summary_kpis_p2[country_summary_kpis_p2['Country'].isin(['Turkey', 'Azerbaijan'])]
        if not tr_az_df_p2.empty: st.dataframe(tr_az_df_p2[cols_to_display_countries].style.format(column_formatters()), use_container_width=True)
        else: st.info("TR veya AZ için veri bulunamadı.")
        st.markdown("##### Global Ortalamalar (TR ve AZ Hariç)")
        df_global_avg_src_p2 = df_p2_processed[~df_p2_processed['Country'].isin(['TR', 'AZ'])]
        if not df_global_avg_src_p2.empty:
            global_total_spent_p2 = df_global_avg_src_p2['Amount spent (USD)'].sum()
            global_total_impressions_p2 = df_global_avg_src_p2['Impressions'].sum()
            global_total_link_clicks_p2 = df_global_avg_src_p2['Link clicks'].sum()
            global_total_reach_p2 = df_global_avg_src_p2['Reach'].sum()
            global_total_results_p2 = df_global_avg_src_p2['Results'].sum()
            global_avg_ctr_p2 = (global_total_link_clicks_p2 / global_total_impressions_p2) * 100 if global_total_impressions_p2 > 0 else 0
            global_avg_cpc_p2 = global_total_spent_p2 / global_total_link_clicks_p2 if global_total_link_clicks_p2 > 0 else 0
            global_avg_cpm_p2 = (global_total_spent_p2 / global_total_impressions_p2) * 1000 if global_total_impressions_p2 > 0 else 0
            global_avg_cost_per_result_p2 = (global_total_spent_p2 / global_total_results_p2) if global_total_results_p2 > 0 else 0
            global_avg_data_p2 = {
                'Metrik': [f'Global Ortalama (TR ve AZ Hariç) - {period2_title}'], 'Toplam Harcama (USD)': [global_total_spent_p2],
                'Toplam Reach': [global_total_reach_p2], 'Toplam Gösterim (Impressions)': [global_total_impressions_p2],
                'Toplam Link Tıklaması': [global_total_link_clicks_p2], 'Toplam Sonuç (Results)': [global_total_results_p2],
                'Ortalama CTR (%)': [global_avg_ctr_p2], 'Ortalama CPC (USD)': [global_avg_cpc_p2],
                'Ortalama CPM (USD)': [global_avg_cpm_p2], 'Ortalama Sonuç Başına Maliyet (USD)': [global_avg_cost_per_result_p2]}
            global_avg_display_df_p2 = pd.DataFrame(global_avg_data_p2)
            st.dataframe(global_avg_display_df_p2.style.format(column_formatters()), use_container_width=True)
        else: st.info(f"Global ortalama için TR/AZ dışında veri bulunamadı ({period2_title}).")
        st.divider()
        # --- Campaign/Ad Set Analysis for Period 2 ---
        display_ad_set_analysis_modified(df_p2_processed, generic_analyze_ad_sets, UNIVERSAL_ID_COLUMN, period2_title)
        st.divider()
        # --- Sales Funnel for Period 2 (29 Mayıs) ---
        if df_sales is not None:
            sales_p2_data = df_sales[df_sales['Period'] == '29 Mayıs']
            display_regional_sales_kpis("29 Mayıs", df_p2_processed, sales_p2_data, country_code_to_name_map)
    else: st.error(f"`{combined_file_p2}` yüklenemedi.")

# Note: Removed st.sidebar.header("Ayarlar") as per user action in previous step.

