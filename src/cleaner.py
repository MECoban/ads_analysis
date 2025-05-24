import pandas as pd
import os

# Kaynak ve hedef dosya yolları
source_csv_file = 'data/BV2-All-10-22 May-Dataları-Global.csv'
cleaned_csv_file = 'data/clean_global.csv'

print(f"--- Veri Temizleme Başlatılıyor: {source_csv_file} -> {cleaned_csv_file} ---")

try:
    df = pd.read_csv(source_csv_file)
    print(f"Kaynak dosya '{source_csv_file}' başarıyla okundu. Satır sayısı: {len(df)}")
except FileNotFoundError:
    print(f"Hata: Kaynak dosya '{source_csv_file}' bulunamadı. Lütfen dosya yolunu kontrol edin.")
    exit()

if df.empty:
    print("Kaynak veri seti boş. İşlem yapılmayacak.")
    exit()

# 'Country' sütununun varlığını kontrol et
if 'Country' not in df.columns:
    print("Hata: 'Country' sütunu kaynak dosyada bulunamadı. Temizleme işlemi yapılamıyor.")
    exit()

# 'Country' sütunu NaN (boş) olan satırları filtrele
cleaned_df = df.dropna(subset=['Country'])

num_removed_rows = len(df) - len(cleaned_df)

print(f"'Country' sütunu boş olan {num_removed_rows} satır veri setinden çıkarıldı.")
print(f"Temizlenmiş veri setindeki yeni satır sayısı: {len(cleaned_df)}")

# Temizlenmiş veriyi yeni CSV dosyasına kaydet (index olmadan)
try:
    # data klasörünün var olup olmadığını kontrol et, yoksa oluştur
    data_directory = os.path.dirname(cleaned_csv_file)
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
        print(f"'{data_directory}' klasörü oluşturuldu.")
        
    cleaned_df.to_csv(cleaned_csv_file, index=False, encoding='utf-8')
    print(f"Temizlenmiş veri başarıyla '{cleaned_csv_file}' dosyasına kaydedildi.")
except Exception as e:
    print(f"Hata: Temizlenmiş veri kaydedilirken bir sorun oluştu: {e}")

print("\n--- Veri Temizleme Tamamlandı ---") 

#aynak dosya (data/BV2-All-10-22 May-Dataları-Global.csv) okundu (20855 satır).
#Country sütunu boş olan 24 satır veri setinden çıkarıldı. (Bu, daha önce tespit ettiğimiz ilk özel satır + diğer 23 satırı içeriyor).Temizlenmiş veri setinde 20831 satır kaldı.
#Temizlenmiş veri data/clean_global.csv dosyasına başarıyla kaydedildi.
#Artık data/clean_global.csv dosyası, sadece Country bilgisi dolu olan satırları içeren, analizleriniz için daha temiz bir veri kaynağıdır.
#Bundan sonraki adımda, global_analyzer.py betiğimizi bu yeni data/clean_global.csv dosyasını kullanacak şekilde güncelleyebilir ve analizleri bu temiz veri üzerinden yapabiliriz. Bu, "Belirsiz Ülke" kategorisini ve onunla ilgili karmaşıklıkları tamamen ortadan kaldıracaktır.
