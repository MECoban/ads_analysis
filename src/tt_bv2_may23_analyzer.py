import pandas as pd
import numpy as np

# --- Yapılandırma ---
# Artık temizlenmiş CSV dosyasını kullanıyoruz
main_csv_file_name = 'data/clean_tt_bv2_may23_global.csv'
target_countries_main = ['TR', 'AZ']
spending_threshold = 100.0 # Eşik 100$ olarak güncellendi
kpi_definitions = {
    'CPC (USD)': 'CPC (cost per link click)',
    'CPM (USD)': 'CPM (cost per 1,000 impressions)',
    'CTR (%)': 'CTR (all)'
}

# --- Yardımcı Fonksiyon ---
def get_kpi_value_for_country(df_kpi_cleaned, country_code, kpi_column_name):
    """Belirli bir ülke için ortalama KPI değerini hesaplar."""
    # Temizlenmiş veri setinde artık Country NaN olan satır beklemiyoruz.
    country_data = df_kpi_cleaned[df_kpi_cleaned['Country'] == country_code]
    
    if country_data.empty or kpi_column_name not in country_data.columns or country_data[kpi_column_name].isnull().all():
        return np.nan
    return country_data[kpi_column_name].mean()

# --- Ana Analiz ---
print(f"--- Analiz Edilen Veri Seti: {main_csv_file_name} ---")

try:
    df = pd.read_csv(main_csv_file_name) # df_original yerine doğrudan df olarak okuyoruz
except FileNotFoundError:
    print(f"Hata: {main_csv_file_name} dosyası bulunamadı. Lütfen dosya yolunu kontrol edin.")
    exit()

if df.empty:
    print("    Veri seti boş.")
    exit()

# Temel sütunların varlığını kontrol et (Country sütunu dolu olmalı)
if 'Country' not in df.columns or 'Amount spent (USD)' not in df.columns:
    print(f"    Temel sütunlar ('Country' veya 'Amount spent (USD)') {main_csv_file_name} içinde bulunamadı. Analiz yapılamıyor.")
    exit()

# Toplam Global Harcama (Temizlenmiş veri üzerinden)
total_global_spend_all_valid_countries = df['Amount spent (USD)'].sum()
print(f"  Genel Toplam Harcama (Tüm Geçerli Ülkeler): ${total_global_spend_all_valid_countries:.2f}")

# Ülke bazlı toplam harcamayı hesapla (Country artık NaN olmamalı)
country_total_spending = df.groupby('Country')['Amount spent (USD)'].sum()

# Harcama eşiğini karşılayan diğer ülkeleri belirle
eligible_other_countries_series = country_total_spending[
    (country_total_spending >= spending_threshold) &
    (~country_total_spending.index.isin(target_countries_main))
]

for kpi_display_name, kpi_column_name in kpi_definitions.items():
    print(f"\n  KPI: {kpi_display_name}")

    if kpi_column_name not in df.columns:
        print(f"    KPI sütunu '{kpi_column_name}' bu veri setinde bulunmuyor.")
        continue

    # KPI hesaplaması için sadece ilgili KPI sütununda NaN olmayanları al
    # Country sütunu zaten dolu olmalı
    df_cleaned_for_kpi = df.dropna(subset=[kpi_column_name])
    
    if df_cleaned_for_kpi.empty:
        print("    Bu KPI için (NaN olmayan KPI değerleri) veri kalmadı.")
        continue

    # 1. Global Ortalama (Tüm Geçerli Ülkeler)
    # Bu grubun harcaması zaten total_global_spend_all_valid_countries
    global_avg_kpi_all = df_cleaned_for_kpi[kpi_column_name].mean()
    label_all_global = f"    Global Ortalama (Tüm Geçerli Ülkeler, Harcama: ${total_global_spend_all_valid_countries:.2f})".ljust(70)
    print(f"{label_all_global} : {global_avg_kpi_all:.2f}" if pd.notnull(global_avg_kpi_all) else f"{label_all_global} : N/A")

    # 2. Global Ortalama (TR ve AZ Hariç)
    df_excluding_tr_az = df_cleaned_for_kpi[~df_cleaned_for_kpi['Country'].isin(target_countries_main)]
    if not df_excluding_tr_az.empty:
        spend_excluding_tr_az = df_excluding_tr_az['Amount spent (USD)'].sum()
        global_avg_kpi_excluding_tr_az = df_excluding_tr_az[kpi_column_name].mean()
        label_excluding_tr_az = f"    Global Ortalama (TR ve AZ Hariç, Harcama: ${spend_excluding_tr_az:.2f})".ljust(70)
        print(f"{label_excluding_tr_az} : {global_avg_kpi_excluding_tr_az:.2f}" if pd.notnull(global_avg_kpi_excluding_tr_az) else f"{label_excluding_tr_az} : N/A (Veri Yok)")
    else:
        print("    Global Ortalama (TR ve AZ Hariç)      : N/A (TR ve AZ dışında veri yok)")

    # 3. TR & AZ Ortalamaları
    for country_code in target_countries_main:
        avg_kpi_value = get_kpi_value_for_country(df_cleaned_for_kpi, country_code, kpi_column_name)
        spending_for_country = country_total_spending.get(country_code, 0)
        label = f"    {country_code} (Toplam Harcama: ${spending_for_country:.2f})".ljust(70)
        print(f"{label} : {avg_kpi_value:.2f}" if pd.notnull(avg_kpi_value) else f"{label} : N/A")
    
    # 4. Diğer Uygun Ülkeler (Yeni eşik ile)
    if not eligible_other_countries_series.empty:
        print(f"    --- Diğer Ülkeler (En Az ${spending_threshold:.0f} Harcama) ---")
        for country_code in sorted(eligible_other_countries_series.index):
            spent_amount = eligible_other_countries_series[country_code]
            avg_kpi_value = get_kpi_value_for_country(df_cleaned_for_kpi, country_code, kpi_column_name)
            label = f"      {country_code} (Harcama: ${spent_amount:.2f})".ljust(70)
            print(f"{label} : {avg_kpi_value:.2f}" if pd.notnull(avg_kpi_value) else f"{label} : N/A")
    else:
        print(f"    (TR ve AZ dışında hiçbir spesifik ülke ${spending_threshold:.0f} harcama eşiğini bireysel olarak karşılamadı)")

print("\n" + "="*75 + "\n") # Çizgi uzunluğunu biraz artırdım
print("Analiz tamamlandı.")

def calculate_kpis_for_analysis(df):
    kpi_df = df.copy()
    cols_to_ensure_numeric = ['Amount spent (USD)', 'Impressions', 'Link clicks', 'Reach', 'Results']
    for col in cols_to_ensure_numeric:
        if col in kpi_df.columns:
            kpi_df[col] = pd.to_numeric(kpi_df[col], errors='coerce').fillna(0)
        else:
            print(f"Warning from global_analyzer: Expected column '{col}' not found in DataFrame. It will be initialized to 0.")
            kpi_df[col] = 0 

    kpi_df['CTR (%)'] = np.where(kpi_df['Impressions'] > 0, (kpi_df['Link clicks'] / kpi_df['Impressions']) * 100, 0)
    kpi_df['CPC (USD)'] = np.where(kpi_df['Link clicks'] > 0, kpi_df['Amount spent (USD)'] / kpi_df['Link clicks'], 0)
    kpi_df['CPM (USD)'] = np.where(kpi_df['Impressions'] > 0, (kpi_df['Amount spent (USD)'] / kpi_df['Impressions']) * 1000, 0)
    return kpi_df

def analyze_ad_sets(input_df, target_countries, filter_type, top_n=5):
    if 'Ad Set Name' not in input_df.columns:
        print("Error from global_analyzer: 'Ad Set Name' column not found in input_df for analyze_ad_sets.")
        return pd.DataFrame(), pd.DataFrame() # Return empty DFs

    if filter_type == 'include':
        df_filtered = input_df[input_df['Country'].isin(target_countries)].copy()
    elif filter_type == 'exclude':
        df_filtered = input_df[~input_df['Country'].isin(target_countries)].copy()
    else:
        print(f"Error from global_analyzer: Invalid filter_type '{filter_type}' in analyze_ad_sets.")
        return pd.DataFrame(), pd.DataFrame()

    if df_filtered.empty:
        return pd.DataFrame(), pd.DataFrame()

    required_metrics = ['Amount spent (USD)', 'Impressions', 'Link clicks', 'Reach', 'Results']
    for metric in required_metrics:
        if metric not in df_filtered.columns:
            # This condition implies the column was missing in the *initial* input_df
            # and was not created by calculate_kpis_for_display (which is good, it shouldn't create ad-hoc source cols)
            print(f"Warning from global_analyzer: Source metric column '{metric}' not found. It will be treated as 0 for aggregation.")
            df_filtered[metric] = 0 
        else:
            # Ensure it's numeric before aggregation, even if calculate_kpis_for_display ran
            df_filtered[metric] = pd.to_numeric(df_filtered[metric], errors='coerce').fillna(0)

    ad_set_summary = df_filtered.groupby('Ad Set Name').agg(
        agg_spent=('Amount spent (USD)', 'sum'),
        agg_impressions=('Impressions', 'sum'),
        agg_link_clicks=('Link clicks', 'sum'),
        agg_reach=('Reach', 'sum'),
        agg_results=('Results', 'sum')
    ).reset_index()

    if ad_set_summary.empty:
        return pd.DataFrame(), pd.DataFrame()

    ad_set_summary_renamed = ad_set_summary.rename(columns={
        'agg_spent': 'Amount spent (USD)',
        'agg_impressions': 'Impressions',
        'agg_link_clicks': 'Link clicks',
        'agg_reach': 'Reach',
        'agg_results': 'Results'
    })

    ad_set_kpis_df = calculate_kpis_for_analysis(ad_set_summary_renamed)
    
    ad_set_kpis_df['Avg. Cost per Result (USD)'] = np.where(
        ad_set_kpis_df['Results'] > 0,
        ad_set_kpis_df['Amount spent (USD)'] / ad_set_kpis_df['Results'],
        0
    )

    ad_set_kpis_df = ad_set_kpis_df.rename(columns={
        'Amount spent (USD)': 'Total Spent (USD)',
        'Impressions': 'Total Impressions',
        'Link clicks': 'Total Link Clicks',
        'Reach': 'Total Reach',
        'Results': 'Total Results'
    })

    top_by_results_df = ad_set_kpis_df.sort_values(by='Total Results', ascending=False).head(top_n)
    top_by_spent_df = ad_set_kpis_df.sort_values(by='Total Spent (USD)', ascending=False).head(top_n)

    return top_by_results_df, top_by_spent_df 