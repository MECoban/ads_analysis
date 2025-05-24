import pandas as pd
import numpy as np

# --- Yapılandırma ---
file1_name = 'data/BV2-All-10-22 May-Dataları-Global.csv'
file2_name = 'data/BV5-All-report-May-10-2025-to-May-22-2025.csv'
target_countries_main = ['TR', 'AZ']
spending_threshold = 200.0
kpi_definitions = {
    'CPC (USD)': 'CPC (cost per link click)',
    'CPM (USD)': 'CPM (cost per 1,000 impressions)',
    'CTR (%)': 'CTR (all)'
}

# --- Yardımcı Fonksiyon ---
def get_kpi_value_for_country(df_kpi_cleaned, country_code, kpi_column_name):
    """Belirli bir ülke için ortalama KPI değerini hesaplar."""
    if country_code is pd.NA or country_code is np.nan:
        country_data = df_kpi_cleaned[df_kpi_cleaned['Country'].isnull()]
    else:
        country_data = df_kpi_cleaned[df_kpi_cleaned['Country'] == country_code]
    
    if country_data.empty or kpi_column_name not in country_data.columns or country_data[kpi_column_name].isnull().all():
        return np.nan
    return country_data[kpi_column_name].mean()

# --- Ana Analiz Döngüsü ---
dataframes_to_analyze = []
try:
    df1 = pd.read_csv(file1_name)
    dataframes_to_analyze.append((file1_name, df1))
except FileNotFoundError:
    print(f"Uyarı: {file1_name} dosyası bulunamadı.")

try:
    df2 = pd.read_csv(file2_name)
    dataframes_to_analyze.append((file2_name, df2))
except FileNotFoundError:
    print(f"Uyarı: {file2_name} dosyası bulunamadı.")

if not dataframes_to_analyze:
    print("Analiz edilecek CSV dosyası bulunamadı. Lütfen dosya yollarını kontrol edin.")
else:
    for fname, df_original in dataframes_to_analyze:
        print(f"--- Analiz Edilen Veri Seti: {fname} ---")
        if df_original.empty:
            print("    Bu veri seti boş.")
            print("\n" + "="*60 + "\n")
            continue
        
        df = df_original.copy()

        if 'Country' not in df.columns or 'Amount spent (USD)' not in df.columns:
            print(f"    Temel sütunlar ('Country' veya 'Amount spent (USD)') {fname} içinde bulunamadı. Bu veri seti atlanıyor.")
            print("\n" + "="*60 + "\n")
            continue

        # Toplam Global Harcama
        total_global_spend = df['Amount spent (USD)'].sum()
        print(f"  Toplam Global Harcama (Tüm Ülkeler)    : ${total_global_spend:.2f}")

        # Ülke bazlı toplam harcamayı hesapla (NaN ülkeleri de içerecek şekilde)
        country_total_spending = df.groupby('Country', dropna=False)['Amount spent (USD)'].sum()
        
        # NaN (Belirsiz) Ülke Harcaması
        nan_country_spending = country_total_spending[country_total_spending.index.isnull()].sum()
        if nan_country_spending > 0:
            print(f"  Belirsiz/Boş Ülke Kodu İçin Harcama   : ${nan_country_spending:.2f}")

        # Harcama eşiğini karşılayan diğer ülkeleri belirle (NaN olmayanlar için)
        eligible_other_countries_series = country_total_spending[
            country_total_spending.index.notnull() &
            (country_total_spending >= spending_threshold) &
            (~country_total_spending.index.isin(target_countries_main))
        ]

        for kpi_display_name, kpi_column_name in kpi_definitions.items():
            print(f"\n  KPI: {kpi_display_name}")

            if kpi_column_name not in df.columns:
                print(f"    KPI sütunu '{kpi_column_name}' bu veri setinde bulunmuyor.")
                continue

            # Mevcut KPI için DataFrame'i temizle (NaN country olanları da koru)
            df_cleaned_for_kpi = df.dropna(subset=[kpi_column_name]) # Sadece KPI sütununda NaN olanları çıkar
            
            if df_cleaned_for_kpi.empty:
                print("    Bu KPI için (NaN olmayan KPI değerleri) veri kalmadı.")
                continue

            # 1. Global Ortalama (Tüm veriler üzerinden)
            global_avg_kpi = df_cleaned_for_kpi[kpi_column_name].mean()
            print(f"    Global Ortalama (Tüm Veriler)        : {global_avg_kpi:.2f}" if pd.notnull(global_avg_kpi) else "    Global Ortalama (Tüm Veriler)        : N/A")

            # 2. TR & AZ Ortalamaları
            for country_code in target_countries_main:
                avg_kpi_value = get_kpi_value_for_country(df_cleaned_for_kpi, country_code, kpi_column_name)
                spending_for_country = country_total_spending.get(country_code, 0)
                label = f"    {country_code} (Toplam Harcama: ${spending_for_country:.2f})".ljust(45)
                print(f"{label} : {avg_kpi_value:.2f}" if pd.notnull(avg_kpi_value) else f"{label} : N/A")
            
            # NaN ülke için KPI (eğer harcaması varsa)
            if nan_country_spending > 0:
                avg_kpi_nan_country = get_kpi_value_for_country(df_cleaned_for_kpi, pd.NA, kpi_column_name)
                label_nan = f"    Belirsiz Ülke (Harcama: ${nan_country_spending:.2f})".ljust(45)
                print(f"{label_nan} : {avg_kpi_nan_country:.2f}" if pd.notnull(avg_kpi_nan_country) else f"{label_nan} : N/A")

            # 3. Diğer Uygun Ülkeler
            if not eligible_other_countries_series.empty:
                print(f"    --- Diğer Ülkeler (En Az ${spending_threshold:.0f} Harcama) ---")
                for country_code in sorted(eligible_other_countries_series.index):
                    spent_amount = eligible_other_countries_series[country_code]
                    avg_kpi_value = get_kpi_value_for_country(df_cleaned_for_kpi, country_code, kpi_column_name)
                    label = f"      {country_code} (Harcama: ${spent_amount:.2f})".ljust(45)
                    print(f"{label} : {avg_kpi_value:.2f}" if pd.notnull(avg_kpi_value) else f"{label} : N/A")
            else:
                # Bu mesajı sadece NaN ülke harcaması yoksa veya TR/AZ dışında harcama yoksa göster
                if not (nan_country_spending > 0 and len(country_total_spending[country_total_spending.index.notnull()]) <= len(target_countries_main)):
                     if not eligible_other_countries_series.any() and not country_total_spending[country_total_spending.index.isin(target_countries_main)].sum() >= spending_threshold:
                        print(f"    (TR ve AZ dışında hiçbir spesifik ülke ${spending_threshold:.0f} harcama eşiğini bireysel olarak karşılamadı)")

        print("\n" + "="*60 + "\n")

print("Analiz tamamlandı.") 