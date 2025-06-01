import streamlit as st
import pandas as pd
import numpy as np
from global_analyzer import analyze_ad_sets # Removed calculate_kpis_for_analysis import as it's not directly used here
from bv5_analyzer import analyze_ad_sets_bv5 # Added import for BV5
from bv5_may23_analyzer import analyze_ad_sets_bv5_may23 # New import
from tt_bv2_may23_analyzer import analyze_ad_sets_tt_bv2_may23 # New import

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

st.title("Facebook Reklam Performans Analizi Dashboard")

tab1_title = "BV2 Analizi (10-22 Mayıs)"
tab2_title = "BV5 Analizi (10-22 Mayıs)"
tab3_title = "BV5 Analizi (23-29 Mayıs)"
tab4_title = "TT BV2 Analizi (23-29 Mayıs)"

tab1, tab2, tab3, tab4 = st.tabs([tab1_title, tab2_title, tab3_title, tab4_title])

with tab1:
    st.header(tab1_title)

    if df_bv2_cleaned is not None:
        st.subheader(f"Veri Temizleme Süreci ({original_bv2_file_name})")
        st.markdown(f"""
        Analizler için kullanılan orijinal `{original_bv2_file_name}` veri seti üzerinde bir temizlik işlemi uygulanmıştır:
        - **`Country` (Ülke) sütununda değeri olmayan satırlar veri setinden çıkarıldı.** Bu işlem, hem Facebook'un otomatik oluşturduğu olası bir genel toplam satırını hem de ülke bilgisi eksik olan diğer münferit satırları kapsamaktadır.
        - Orijinal veri setinde **20,855 satır** bulunuyordu.
        - Temizlik işlemi sonucunda **24 satır çıkarılarak** veri seti **20,831 satıra** düşürüldü.
        - Bu temizlenmiş ve analize hazır veri, `data/clean_global.csv` dosyasına kaydedilmiştir.
        
        Bu ön işleme adımı, analizlerimizin yalnızca geçerli ve tanımlı ülke verilerine dayanmasını sağlayarak daha doğru ve güvenilir sonuçlar elde etmemize olanak tanımıştır.
        """)
        st.divider()

        st.subheader("Detaylı KPI Analizleri (BV2 - Temizlenmiş Veri)")
        
        # Process the raw cleaned data once for base metrics needed for various analyses
        # This df_bv2_processed will be the input for country summaries and ad set analyses
        df_bv2_processed = calculate_kpis_for_display(df_bv2_cleaned.copy()) # Use the renamed display-focused KPI function

        # --- Country-Level Analysis --- 
        country_summary_agg = df_bv2_processed.groupby('Country').agg(
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
        country_summary_kpis = calculate_kpis_for_display(country_summary_for_kpis) # Use display KPI func
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

        # 1. Display countries with spending over the threshold
        spending_threshold = 100
        st.markdown(f"#### Harcaması {spending_threshold} USD Üzerinde Olan Ülkeler ve KPI'ları")
        top_countries_df = country_summary_kpis[country_summary_kpis['Total Spent (USD)'] > spending_threshold]
        
        cols_to_display_countries = ['Country', 'Total Spent (USD)', 'Total Reach', 'Total Link Clicks', 'Total Results', 'CTR (%)', 'CPC (USD)', 'CPM (USD)', 'Avg. Cost per Result (USD)']
        style_format_countries = {
            "Total Spent (USD)": "${:,.2f}",
            "Total Reach": "{:,.0f}",
            "Total Link Clicks": "{:,.0f}",
            "Total Results": "{:,.0f}",
            "CTR (%)": "{:.2f}%",
            "CPC (USD)": "${:,.2f}",
            "CPM (USD)": "${:,.2f}",
            "Avg. Cost per Result (USD)": "${:,.2f}"
        }

        if not top_countries_df.empty:
            display_top_countries_df = top_countries_df.copy()
            display_top_countries_df['Country'] = display_top_countries_df['Country'].map(country_code_to_name_map).fillna(display_top_countries_df['Country'])
            st.dataframe(display_top_countries_df[cols_to_display_countries].style.format(style_format_countries), use_container_width=True)
        else:
            st.info(f"Belirtilen harcama ({spending_threshold} USD) üzerinde ülke bulunamadı.")

        # 2. KPIs for Turkey (TR) and Azerbaijan (AZ)
        st.markdown("#### Türkiye (TR) ve Azerbaycan (AZ) için Özel KPI Değerleri")
        tr_az_countries_df = country_summary_kpis[country_summary_kpis['Country'].isin(['TR', 'AZ'])]
        
        if not tr_az_countries_df.empty:
            display_tr_az_df = tr_az_countries_df.copy()
            display_tr_az_df['Country'] = display_tr_az_df['Country'].map(country_code_to_name_map).fillna(display_tr_az_df['Country'])
            st.dataframe(display_tr_az_df[cols_to_display_countries].style.format(style_format_countries), use_container_width=True)
        else:
            st.info("Veri setinde Türkiye (TR) veya Azerbaycan (AZ) için tanımlı harcama bilgisi bulunamadı veya harcamalar belirtilen eşiklerin altında.")

        # 3. Global Averages (excluding TR and AZ)
        st.markdown("#### Global Ortalamalar (Türkiye ve Azerbaycan Hariç)")
        df_global_avg_source = df_bv2_processed[~df_bv2_processed['Country'].isin(['TR', 'AZ'])]
        
        if not df_global_avg_source.empty:
            global_total_spent = df_global_avg_source['Amount spent (USD)'].sum()
            global_total_impressions = df_global_avg_source['Impressions'].sum()
            global_total_link_clicks = df_global_avg_source['Link clicks'].sum()
            global_total_reach = df_global_avg_source['Reach'].sum()
            global_total_results = df_global_avg_source['Results'].sum()

            global_avg_ctr = (global_total_link_clicks / global_total_impressions) * 100 if global_total_impressions > 0 else 0
            global_avg_cpc = global_total_spent / global_total_link_clicks if global_total_link_clicks > 0 else 0
            global_avg_cpm = (global_total_spent / global_total_impressions) * 1000 if global_total_impressions > 0 else 0
            global_avg_cost_per_result = (global_total_spent / global_total_results) if global_total_results > 0 else 0

            global_avg_data = {
                'Metrik': ['Global Ortalama (TR ve AZ Hariç)'],
                'Toplam Harcama (USD)': [global_total_spent],
                'Toplam Reach': [global_total_reach],
                'Toplam Gösterim (Impressions)': [global_total_impressions],
                'Toplam Link Tıklaması': [global_total_link_clicks],
                'Toplam Sonuç (Results)': [global_total_results],
                'Ortalama CTR (%)': [global_avg_ctr],
                'Ortalama CPC (USD)': [global_avg_cpc],
                'Ortalama CPM (USD)': [global_avg_cpm],
                'Ortalama Sonuç Başına Maliyet (USD)': [global_avg_cost_per_result]
            }
            global_avg_display_df = pd.DataFrame(global_avg_data)
            st.dataframe(global_avg_display_df.style.format({
                "Toplam Harcama (USD)": "${:,.2f}",
                "Toplam Reach": "{:,.0f}",
                "Toplam Gösterim (Impressions)": "{:,.0f}",
                "Toplam Link Tıklaması": "{:,.0f}",
                "Toplam Sonuç (Results)": "{:,.0f}",
                "Ortalama CTR (%)": "{:.2f}%",
                "Ortalama CPC (USD)": "${:,.2f}",
                "Ortalama CPM (USD)": "${:,.2f}",
                "Ortalama Sonuç Başına Maliyet (USD)": "${:,.2f}",
            }), use_container_width=True)
        else:
            st.info("TR ve AZ dışındaki ülkeler için global ortalama hesaplanacak veri bulunamadı.")

        # --- Ad Set Analysis Section ---
        st.divider()
        st.header("Reklam Seti Bazlı KPI Analizleri (BV2 - Temizlenmiş Veri)")

        if 'Ad Set Name' in df_bv2_processed.columns: # Check in the processed dataframe
            tr_name = country_code_to_name_map.get('TR', 'TR')
            az_name = country_code_to_name_map.get('AZ', 'AZ')
            top_n_ad_sets = 10 # Changed from 5 to 10

            cols_to_display_ad_sets = ['Ad Set Name', 'Total Spent (USD)', 'Total Reach', 'Total Link Clicks', 'Total Results', 'CTR (%)', 'CPC (USD)', 'CPM (USD)', 'Avg. Cost per Result (USD)']
            style_format_ad_sets = style_format_countries # Can reuse the same style format

            # Helper for displaying ad set tables
            def display_ad_set_analysis_tables(results_df, spent_df, label):
                st.markdown(f"##### En Çok Sonuç Getiren İlk {top_n_ad_sets} Reklam Seti ({label})")
                if results_df is not None and not results_df.empty:
                    st.dataframe(results_df[cols_to_display_ad_sets].style.format(style_format_ad_sets), use_container_width=True)
                else:
                    st.info(f"Sonuçlara göre sıralanacak reklam seti bulunamadı ({label}).")
                
                st.markdown(f"##### En Çok Harcama Yapan İlk {top_n_ad_sets} Reklam Seti ({label})")
                if spent_df is not None and not spent_df.empty:
                    st.dataframe(spent_df[cols_to_display_ad_sets].style.format(style_format_ad_sets), use_container_width=True)
                else:
                    st.info(f"Harcamalara göre sıralanacak reklam seti bulunamadı ({label}).")
                st.caption(f"Not: Yukarıdaki reklam seti analizleri {label} için geçerlidir.")
                st.divider()

            st.markdown(f"#### {tr_name} Reklam Seti Performansı")
            tr_results_df, tr_spent_df = analyze_ad_sets(df_bv2_processed, target_countries=['TR'], filter_type='include', top_n=top_n_ad_sets)
            display_ad_set_analysis_tables(tr_results_df, tr_spent_df, tr_name)

            st.markdown(f"#### {az_name} Reklam Seti Performansı")
            az_results_df, az_spent_df = analyze_ad_sets(df_bv2_processed, target_countries=['AZ'], filter_type='include', top_n=top_n_ad_sets)
            display_ad_set_analysis_tables(az_results_df, az_spent_df, az_name)
            
            global_label = f"Global ({tr_name} ve {az_name} Hariç)"
            st.markdown(f"#### {global_label} Reklam Seti Performansı")
            global_results_df, global_spent_df = analyze_ad_sets(df_bv2_processed, target_countries=['TR', 'AZ'], filter_type='exclude', top_n=top_n_ad_sets)
            display_ad_set_analysis_tables(global_results_df, global_spent_df, global_label)

        else:
            st.warning("`Ad Set Name` sütunu veri setinde (`data/clean_global.csv`) bulunamadığı için reklam seti bazlı analizler yapılamıyor. Lütfen CSV dosyanızı kontrol edin.")

    else:
        st.error(f"`{cleaned_bv2_file}` dosyası yüklenemediği için BV2 analizleri gösterilemiyor. Lütfen dosyanın `data` klasöründe olduğundan ve doğru formatta olduğundan emin olun.")

with tab2:
    st.header(tab2_title)
    st.markdown(f"""
    Bu sekme, `{bv5_file_name}` adlı veri setine ait analizler için ayrılmıştır.
    """) # Keep existing intro for tab2

    if df_bv5_cleaned is not None:
        # Display BV5 data cleaning summary (using placeholder numbers for now, as cleaner script output is not directly captured here)
        # In a real scenario, these numbers would come from the bv5_cleaner.py execution log or by reading the file
        original_bv5_rows = 8396 # Placeholder, actual: 8396
        cleaned_bv5_rows = 8390  # Placeholder, actual: 8390
        removed_bv5_rows = original_bv5_rows - cleaned_bv5_rows

        st.subheader(f"Veri Temizleme Süreci ({original_bv5_file_name})")
        st.markdown(f"""
        Analizler için kullanılan orijinal `{original_bv5_file_name}` veri seti üzerinde bir temizlik işlemi uygulanmıştır:
        - **`Country` (Ülke) sütununda değeri olmayan satırlar veri setinden çıkarıldı.**
        - Orijinal veri setinde **{original_bv5_rows:,} satır** bulunuyordu.
        - Temizlik işlemi sonucunda **{removed_bv5_rows:,} satır çıkarılarak** veri seti **{cleaned_bv5_rows:,} satıra** düşürüldü.
        - Bu temizlenmiş ve analize hazır veri, `{cleaned_bv5_file}` dosyasına kaydedilmiştir.
        
        Bu ön işleme adımı, analizlerimizin yalnızca geçerli ve tanımlı ülke verilerine dayanmasını sağlayarak daha doğru ve güvenilir sonuçlar elde etmemize olanak tanımıştır.
        """)
        st.divider()

        st.subheader("Detaylı KPI Analizleri (BV5 - Temizlenmiş Veri)")
        
        df_bv5_processed = calculate_kpis_for_display(df_bv5_cleaned.copy())

        # --- BV5 Country-Level Analysis (mirroring BV2) ---
        bv5_country_summary_agg = df_bv5_processed.groupby('Country').agg(
            total_spent=('Amount spent (USD)', 'sum'),
            total_impressions=('Impressions', 'sum'),
            total_link_clicks=('Link clicks', 'sum'),
            total_reach=('Reach', 'sum'),
            total_results=('Results', 'sum')
        ).reset_index()

        bv5_country_summary_for_kpis = bv5_country_summary_agg.rename(columns={
            'total_spent': 'Amount spent (USD)',
            'total_impressions': 'Impressions',
            'total_link_clicks': 'Link clicks',
            'total_reach': 'Reach',
            'total_results': 'Results'
        })
        bv5_country_summary_kpis = calculate_kpis_for_display(bv5_country_summary_for_kpis)
        bv5_country_summary_kpis['Avg. Cost per Result (USD)'] = np.where(
            bv5_country_summary_kpis['Results'] > 0, 
            bv5_country_summary_kpis['Amount spent (USD)'] / bv5_country_summary_kpis['Results'], 0)
        bv5_country_summary_kpis = bv5_country_summary_kpis.rename(columns={
            'Amount spent (USD)': 'Total Spent (USD)',
            'Impressions': 'Total Impressions',
            'Link clicks': 'Total Link Clicks',
            'Reach': 'Total Reach',
            'Results': 'Total Results'
        }).sort_values(by='Total Spent (USD)', ascending=False)

        # 1. Display BV5 countries with spending over the threshold
        # Using the same spending_threshold and display columns/styles as BV2 for consistency
        st.markdown(f"#### Harcaması {spending_threshold} USD Üzerinde Olan Ülkeler ve KPI'ları (BV5)")
        bv5_top_countries_df = bv5_country_summary_kpis[bv5_country_summary_kpis['Total Spent (USD)'] > spending_threshold]
        
        if not bv5_top_countries_df.empty:
            bv5_display_top_countries_df = bv5_top_countries_df.copy()
            bv5_display_top_countries_df['Country'] = bv5_display_top_countries_df['Country'].map(country_code_to_name_map).fillna(bv5_display_top_countries_df['Country'])
            st.dataframe(bv5_display_top_countries_df[cols_to_display_countries].style.format(style_format_countries), use_container_width=True)
        else:
            st.info(f"Belirtilen harcama ({spending_threshold} USD) üzerinde ülke bulunamadı (BV5)." )

        # 2. BV5 KPIs for Turkey (TR) and Azerbaijan (AZ)
        st.markdown("#### Türkiye (TR) ve Azerbaycan (AZ) için Özel KPI Değerleri (BV5)")
        bv5_tr_az_countries_df = bv5_country_summary_kpis[bv5_country_summary_kpis['Country'].isin(['TR', 'AZ'])]
        
        if not bv5_tr_az_countries_df.empty:
            bv5_display_tr_az_df = bv5_tr_az_countries_df.copy()
            bv5_display_tr_az_df['Country'] = bv5_display_tr_az_df['Country'].map(country_code_to_name_map).fillna(bv5_display_tr_az_df['Country'])
            st.dataframe(bv5_display_tr_az_df[cols_to_display_countries].style.format(style_format_countries), use_container_width=True)
        else:
            st.info("Veri setinde Türkiye (TR) veya Azerbaycan (AZ) için tanımlı harcama bilgisi bulunamadı veya harcamalar belirtilen eşiklerin altında (BV5).")

        # 3. BV5 Global Averages (excluding TR and AZ)
        st.markdown("#### Global Ortalamalar (Türkiye ve Azerbaycan Hariç) (BV5)")
        bv5_df_global_avg_source = df_bv5_processed[~df_bv5_processed['Country'].isin(['TR', 'AZ'])]
        
        if not bv5_df_global_avg_source.empty:
            bv5_global_total_spent = bv5_df_global_avg_source['Amount spent (USD)'].sum()
            bv5_global_total_impressions = bv5_df_global_avg_source['Impressions'].sum()
            bv5_global_total_link_clicks = bv5_df_global_avg_source['Link clicks'].sum()
            bv5_global_total_reach = bv5_df_global_avg_source['Reach'].sum()
            bv5_global_total_results = bv5_df_global_avg_source['Results'].sum()

            bv5_global_avg_ctr = (bv5_global_total_link_clicks / bv5_global_total_impressions) * 100 if bv5_global_total_impressions > 0 else 0
            bv5_global_avg_cpc = bv5_global_total_spent / bv5_global_total_link_clicks if bv5_global_total_link_clicks > 0 else 0
            bv5_global_avg_cpm = (bv5_global_total_spent / bv5_global_total_impressions) * 1000 if bv5_global_total_impressions > 0 else 0
            bv5_global_avg_cost_per_result = (bv5_global_total_spent / bv5_global_total_results) if bv5_global_total_results > 0 else 0

            bv5_global_avg_data = {
                'Metrik': ['Global Ortalama (TR ve AZ Hariç) - BV5'],
                'Toplam Harcama (USD)': [bv5_global_total_spent],
                'Toplam Reach': [bv5_global_total_reach],
                'Toplam Gösterim (Impressions)': [bv5_global_total_impressions],
                'Toplam Link Tıklaması': [bv5_global_total_link_clicks],
                'Toplam Sonuç (Results)': [bv5_global_total_results],
                'Ortalama CTR (%)': [bv5_global_avg_ctr],
                'Ortalama CPC (USD)': [bv5_global_avg_cpc],
                'Ortalama CPM (USD)': [bv5_global_avg_cpm],
                'Ortalama Sonuç Başına Maliyet (USD)': [bv5_global_avg_cost_per_result]
            }
            bv5_global_avg_display_df = pd.DataFrame(bv5_global_avg_data)
            # Reusing style_format_countries for the global average table, assuming columns match
            st.dataframe(bv5_global_avg_display_df.style.format({
                "Toplam Harcama (USD)": "${:,.2f}",
                "Toplam Reach": "{:,.0f}",
                "Toplam Gösterim (Impressions)": "{:,.0f}",
                "Toplam Link Tıklaması": "{:,.0f}",
                "Toplam Sonuç (Results)": "{:,.0f}",
                "Ortalama CTR (%)": "{:.2f}%",
                "Ortalama CPC (USD)": "${:,.2f}",
                "Ortalama CPM (USD)": "${:,.2f}",
                "Ortalama Sonuç Başına Maliyet (USD)": "${:,.2f}",
            }), use_container_width=True)
        else:
            st.info("TR ve AZ dışındaki ülkeler için global ortalama hesaplanacak veri bulunamadı (BV5)." )

        # --- BV5 Ad Set Analysis Section (mirroring BV2) ---
        st.divider()
        st.header("Reklam Seti Bazlı KPI Analizleri (BV5 - Temizlenmiş Veri)")

        if 'Ad Set Name' in df_bv5_processed.columns:
            tr_name = country_code_to_name_map.get('TR', 'TR')
            az_name = country_code_to_name_map.get('AZ', 'AZ')
            # top_n_ad_sets is already defined in BV2 section, reusing it (value is 10)

            # Reusing cols_to_display_ad_sets and style_format_ad_sets from BV2 section

            # Using the same helper function display_ad_set_analysis_tables from BV2 section
            # Ensure it is defined in a scope accessible here or redefine/pass as parameter if needed.
            # For simplicity, assuming it's accessible or we would redefine it here if it were complex.
            # Since display_ad_set_analysis_tables is defined within tab1, it's not directly accessible.
            # We need to either define it globally, pass it, or redefine it for tab2.
            # For this edit, I will redefine a similar helper function for BV5 to keep changes localized to tab2.

            def display_bv5_ad_set_analysis_tables(results_df, spent_df, label):
                st.markdown(f"##### En Çok Sonuç Getiren İlk {top_n_ad_sets} Reklam Seti ({label} - BV5)")
                if results_df is not None and not results_df.empty:
                    st.dataframe(results_df[cols_to_display_ad_sets].style.format(style_format_ad_sets), use_container_width=True)
                else:
                    st.info(f"Sonuçlara göre sıralanacak reklam seti bulunamadı ({label} - BV5)." )
                
                st.markdown(f"##### En Çok Harcama Yapan İlk {top_n_ad_sets} Reklam Seti ({label} - BV5)")
                if spent_df is not None and not spent_df.empty:
                    st.dataframe(spent_df[cols_to_display_ad_sets].style.format(style_format_ad_sets), use_container_width=True)
                else:
                    st.info(f"Harcamalara göre sıralanacak reklam seti bulunamadı ({label} - BV5)." )
                st.caption(f"Not: Yukarıdaki reklam seti analizleri {label} (BV5) için geçerlidir.")
                st.divider()

            st.markdown(f"#### {tr_name} Reklam Seti Performansı (BV5)")
            bv5_tr_results_df, bv5_tr_spent_df = analyze_ad_sets_bv5(df_bv5_processed, target_countries=['TR'], filter_type='include', top_n=top_n_ad_sets)
            display_bv5_ad_set_analysis_tables(bv5_tr_results_df, bv5_tr_spent_df, tr_name)

            st.markdown(f"#### {az_name} Reklam Seti Performansı (BV5)")
            bv5_az_results_df, bv5_az_spent_df = analyze_ad_sets_bv5(df_bv5_processed, target_countries=['AZ'], filter_type='include', top_n=top_n_ad_sets)
            display_bv5_ad_set_analysis_tables(bv5_az_results_df, bv5_az_spent_df, az_name)
            
            bv5_global_label = f"Global ({tr_name} ve {az_name} Hariç) - BV5"
            st.markdown(f"#### {bv5_global_label} Reklam Seti Performansı")
            bv5_global_results_df, bv5_global_spent_df = analyze_ad_sets_bv5(df_bv5_processed, target_countries=['TR', 'AZ'], filter_type='exclude', top_n=top_n_ad_sets)
            display_bv5_ad_set_analysis_tables(bv5_global_results_df, bv5_global_spent_df, bv5_global_label)

        else:
            st.warning(f"`Ad Set Name` sütunu BV5 veri setinde (`{cleaned_bv5_file}`) bulunamadığı için reklam seti bazlı analizler yapılamıyor.")

    else:
        st.error(f"`{cleaned_bv5_file}` dosyası yüklenemediği için BV5 analizleri gösterilemiyor. Lütfen dosyanın `data` klasöründe olduğundan ve doğru formatta olduğundan emin olun.")
    # The old descriptive markdown for tab2 has been replaced by the actual analysis.
    # Remove or comment out the old markdown if it was extensive and is no longer needed.
    # The initial part of the old markdown is kept ("Bu sekme, ... ayrılmıştır.")

with tab3: # New tab for BV5 May 23-29
    st.header(tab3_title)
    if df_bv5_may23_cleaned is not None and not df_bv5_may23_cleaned.empty:
        st.markdown(f"**Orjinal Dosya:** `{original_bv5_may23_file_name}`")
        st.markdown(f"**Temizlenmiş Dosya:** `{cleaned_bv5_may23_file}`")
        
        original_rows_bv5_may23 = get_original_row_count(f"data/{original_bv5_may23_file_name}")
        cleaned_rows_bv5_may23 = len(df_bv5_may23_cleaned)
        display_cleaning_info(original_rows_bv5_may23, cleaned_rows_bv5_may23, "BV5 (23-29 Mayıs)")

        st.subheader("Ülke Bazlı KPI'lar (BV5 23-29 Mayıs)")
        kpis_to_show_bv5_may23 = prepare_country_kpis(df_bv5_may23_cleaned, dataset_name="BV5 (23-29 Mayıs)")
        st.dataframe(kpis_to_show_bv5_may23.style.format(formatter=column_formatters()))
        
        display_ad_set_analysis(df_bv5_may23_cleaned, analyze_ad_sets_bv5_may23, "BV5 (23-29 Mayıs)")
    else:
        st.error(f"Temizlenmiş BV5 (23-29 Mayıs) verisi ({cleaned_bv5_may23_file}) yüklenemedi veya boş.")

with tab4: # New tab for TT BV2 May 23-29
    st.header(tab4_title)
    if df_tt_bv2_may23_cleaned is not None and not df_tt_bv2_may23_cleaned.empty:
        st.markdown(f"**Orjinal Dosya:** `{original_tt_bv2_may23_file_name}`")
        st.markdown(f"**Temizlenmiş Dosya:** `{cleaned_tt_bv2_may23_file}`")
        
        original_rows_tt_bv2_may23 = get_original_row_count(f"data/{original_tt_bv2_may23_file_name}")
        cleaned_rows_tt_bv2_may23 = len(df_tt_bv2_may23_cleaned)
        display_cleaning_info(original_rows_tt_bv2_may23, cleaned_rows_tt_bv2_may23, "TT BV2 (23-29 Mayıs)")

        st.subheader("Ülke Bazlı KPI'lar (TT BV2 23-29 Mayıs)")
        kpis_to_show_tt_bv2_may23 = prepare_country_kpis(df_tt_bv2_may23_cleaned, dataset_name="TT BV2 (23-29 Mayıs)")
        st.dataframe(kpis_to_show_tt_bv2_may23.style.format(formatter=column_formatters()))
        
        # For TT BV2, we use the same logic as the original BV2 (global_analyzer's analyze_ad_sets)
        # but with the new analyzer function that has a different name
        display_ad_set_analysis(df_tt_bv2_may23_cleaned, analyze_ad_sets_tt_bv2_may23, "TT BV2 (23-29 Mayıs)")
    else:
        st.error(f"Temizlenmiş TT BV2 (23-29 Mayıs) verisi ({cleaned_tt_bv2_may23_file}) yüklenemedi veya boş.")

st.sidebar.header("Ayarlar")
