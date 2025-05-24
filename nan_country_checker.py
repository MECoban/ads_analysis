import pandas as pd

# Analiz edilecek CSV dosyası
csv_file_name = 'data/BV2-All-10-22 May-Dataları-Global.csv'

print(f"--- 'Country' Sütunu Boş Olan Satırların Harcama Kontrolü (İlk Satır Hariç): {csv_file_name} ---")

try:
    df = pd.read_csv(csv_file_name)
except FileNotFoundError:
    print(f"Hata: {csv_file_name} dosyası bulunamadı. Lütfen dosya yolunu kontrol edin.")
    exit()

if df.empty:
    print("Veri seti boş.")
    exit()

# İlk satırın 'Country' değerinin NaN olup olmadığını kontrol et
is_first_row_nan_country = False
if not df.empty:
    is_first_row_nan_country = pd.isna(df.iloc[0]['Country'])

# Country sütunu NaN olan satırları al
nan_country_rows_all = df[df['Country'].isnull()]

# Eğer ilk satırın Country değeri NaN ise, bu satırı çıkarılmış_nan_ülke_satırları listesinden çıkar
if is_first_row_nan_country and not nan_country_rows_all.empty:
    # Sadece ilk satır NaN ise ve diğer NaN country satırları yoksa, boş bir df kalır
    # Eğer nan_country_rows_all sadece ilk satırdan oluşuyorsa, iloc[1:] hata verir.
    # Bu yüzden, nan_country_rows_all DataFrame'inin index'inin, df'in ilk satırının index'i ile eşleşip eşleşmediğine bakmak daha güvenli.
    if nan_country_rows_all.index[0] == df.index[0]: # İlk NaN satırı gerçekten df'in ilk satırı mı?
        other_nan_country_rows = nan_country_rows_all.iloc[1:]
    else: # Bu durum pek olası değil ama bir güvenlik önlemi
        other_nan_country_rows = nan_country_rows_all
else:
    other_nan_country_rows = nan_country_rows_all

num_other_nan_country_rows = len(other_nan_country_rows)

if is_first_row_nan_country:
    print(f"Bilgi: İlk satırın 'Country' değeri boş (NaN) ve analizden hariç tutuluyor.")

print(f"İlk satır hariç 'Country' sütunu boş (NaN) olan satır sayısı: {num_other_nan_country_rows}")

if num_other_nan_country_rows > 0:
    if 'Amount spent (USD)' in other_nan_country_rows.columns:
        total_spent_other_nan_countries = other_nan_country_rows['Amount spent (USD)'].sum()
        print(f"Bu {num_other_nan_country_rows} satırın toplam 'Amount spent (USD)' değeri: ${total_spent_other_nan_countries:.2f}")
        
        print("\nBu satırlardan ilk birkaçı (en fazla 5):")
        print(other_nan_country_rows.head())
    else:
        print("Uyarı: 'Amount spent (USD)' sütunu bu satırlarda bulunamadı.")
elif not is_first_row_nan_country and num_other_nan_country_rows == 0 and not nan_country_rows_all.empty() : #ilk satir nan degil ve baska da nan yok
    print("İlk satırın 'Country' değeri dolu, ancak 'Country' sütunu boş olan başka satır bulunmamaktadır.")
else:
    print("İlk satır hariç 'Country' sütunu boş olan başka satır bulunmamaktadır.")

print("\n" + "="*50 + "\nKontrol tamamlandı.") 