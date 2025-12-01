# Doğal Dilden SQL Sorgusu Oluşturucu (Text-to-SQL)

NLP Dersi Projesi - Türkçe doğal dil sorgularını SQL sorgularına çeviren bir uygulama.

## 🎯 Amaç

SQL bilmeyen kullanıcıların Türkçe sorular sorarak veritabanından veri çekmesini sağlamak.

Örnek:
- Kullanıcı: *"Geçen ay en çok satış yapan 5 ürünü listele"*
- Sistem: SQL sorgusunu oluşturur ve sonucu tablo olarak gösterir

## 🛠 Kullanılan Teknolojiler

- **Python 3.8+**
- **OpenAI API** - GPT-3.5-turbo modeli ile doğal dil işleme
- **SQLite** - Örnek veritabanı
- **tabulate** - Tablo formatında çıktı

## 📁 Proje Yapısı

```
NLPDers/
├── text_to_sql.py      # Ana uygulama
├── setup_database.py   # Veritabanı oluşturma scripti
├── requirements.txt    # Python bağımlılıkları
├── .env.example        # Örnek ortam değişkenleri dosyası
└── README.md           # Bu dosya
```

## 🗄 Veritabanı Şeması

Örnek veritabanı bir e-ticaret senaryosunu simüle eder:

```
kategoriler (id, kategori_adi)
     │
     └─── urunler (id, urun_adi, fiyat, stok_miktari, kategori_id)
               │
               └─── satislar (id, urun_id, musteri_id, miktar, toplam_tutar, satis_tarihi)
                         │
musteriler (id, ad, soyad, email, sehir) ───┘
```

## 🚀 Kurulum

1. **Repoyu klonlayın:**
   ```bash
   git clone https://github.com/yazctahsin/NLPDers.git
   cd NLPDers
   ```

2. **Bağımlılıkları yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

3. **OpenAI API anahtarını ayarlayın:**
   ```bash
   cp .env.example .env
   # .env dosyasını düzenleyip API anahtarınızı ekleyin
   ```

4. **Veritabanını oluşturun:**
   ```bash
   python setup_database.py
   ```

## 💻 Kullanım

### Demo Modu (API anahtarı gerektirmez)
Örnek sorguları veritabanında çalıştırır:
```bash
python text_to_sql.py --demo
```

### Etkileşimli Mod
Kendi sorularınızı sorun:
```bash
python text_to_sql.py --interactive
```

### Tek Sorgu Modu
```bash
python text_to_sql.py "En pahalı 3 ürünü göster"
```

## 📝 Örnek Sorgular

| Türkçe Soru | Açıklama |
|-------------|----------|
| "En çok satış yapan 5 ürünü listele" | Satış miktarına göre en popüler ürünler |
| "İstanbul'daki müşterileri göster" | Şehre göre filtreleme |
| "Elektronik kategorisindeki ürünleri fiyata göre sırala" | Kategori ve sıralama |
| "Geçen ay toplam satış ne kadar?" | Tarih bazlı analiz |
| "Her kategoride kaç ürün var?" | Gruplama ve sayma |
| "Stok miktarı 50'den az olan ürünler" | Koşullu filtreleme |

## 🔧 Sistem Çalışma Prensibi

1. **Şema Tanıtımı:** Veritabanı şeması LLM'e system prompt olarak verilir
2. **Kullanıcı Girişi:** Türkçe doğal dil sorgusu alınır
3. **SQL Dönüşümü:** LLM sorguyu SQL koduna çevirir
4. **Güvenlik Kontrolü:** Sadece SELECT sorguları kabul edilir
5. **Çalıştırma:** SQL sorgusu veritabanında çalıştırılır
6. **Sonuç Gösterimi:** Sonuçlar tablo formatında gösterilir

## ⚠️ Güvenlik

- Sadece `SELECT` sorguları çalıştırılır
- `INSERT`, `UPDATE`, `DELETE`, `DROP` gibi tehlikeli komutlar engellenir
- Kullanıcı girişleri doğrudan SQL'e gönderilmez

## 📋 Demo Çıktı Örneği

```
============================================================
Türkçe Soru: En çok satış yapan 5 ürünü listele
============================================================

Oluşturulan SQL:
SELECT u.urun_adi, SUM(s.miktar) as toplam_satis
FROM urunler u
JOIN satislar s ON u.id = s.urun_id
GROUP BY u.id, u.urun_adi
ORDER BY toplam_satis DESC
LIMIT 5

+------------------+----------------+
| urun_adi         | toplam_satis   |
+==================+================+
| Yoga Matı        | 75             |
| Futbol Topu      | 68             |
| Bluetooth Kulaklık| 64            |
| Çocuk Kitabı     | 62             |
| Erkek T-Shirt    | 58             |
+------------------+----------------+

Toplam 5 kayıt bulundu.
```

## 📄 Lisans

Bu proje eğitim amaçlıdır.
