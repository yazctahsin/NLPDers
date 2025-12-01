"""
Örnek SQLite veritabanı oluşturma scripti.
Bu script, Text-to-SQL projesinde kullanılacak örnek veritabanını oluşturur.
"""

import sqlite3
from datetime import datetime, timedelta
import random

def create_database():
    """Örnek veritabanını oluşturur ve örnek verilerle doldurur."""
    
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    
    # Tabloları oluştur
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kategoriler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kategori_adi TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urun_adi TEXT NOT NULL,
            fiyat REAL NOT NULL,
            stok_miktari INTEGER NOT NULL,
            kategori_id INTEGER,
            FOREIGN KEY (kategori_id) REFERENCES kategoriler(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS musteriler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            soyad TEXT NOT NULL,
            email TEXT,
            sehir TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS satislar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urun_id INTEGER NOT NULL,
            musteri_id INTEGER NOT NULL,
            miktar INTEGER NOT NULL,
            toplam_tutar REAL NOT NULL,
            satis_tarihi DATE NOT NULL,
            FOREIGN KEY (urun_id) REFERENCES urunler(id),
            FOREIGN KEY (musteri_id) REFERENCES musteriler(id)
        )
    ''')
    
    # Kategorileri ekle
    kategoriler = [
        ('Elektronik',),
        ('Giyim',),
        ('Kitap',),
        ('Ev & Yaşam',),
        ('Spor',)
    ]
    cursor.executemany('INSERT OR IGNORE INTO kategoriler (kategori_adi) VALUES (?)', kategoriler)
    
    # Ürünleri ekle
    urunler = [
        ('iPhone 15', 54999.99, 50, 1),
        ('Samsung Galaxy S24', 44999.99, 75, 1),
        ('MacBook Air M2', 69999.99, 30, 1),
        ('AirPods Pro', 9999.99, 100, 1),
        ('Bluetooth Kulaklık', 1499.99, 200, 1),
        ('Erkek T-Shirt', 299.99, 500, 2),
        ('Kadın Elbise', 599.99, 300, 2),
        ('Kot Pantolon', 449.99, 400, 2),
        ('Spor Ayakkabı', 1299.99, 250, 2),
        ('Kış Montu', 2499.99, 150, 2),
        ('Python Programlama', 149.99, 100, 3),
        ('Yapay Zeka', 199.99, 80, 3),
        ('Veri Bilimi', 179.99, 90, 3),
        ('Roman Seti', 299.99, 120, 3),
        ('Çocuk Kitabı', 79.99, 200, 3),
        ('Koltuk Takımı', 24999.99, 20, 4),
        ('Yatak Örtüsü', 799.99, 100, 4),
        ('Mutfak Seti', 1499.99, 60, 4),
        ('Aydınlatma', 599.99, 80, 4),
        ('Halı', 2999.99, 40, 4),
        ('Koşu Bandı', 14999.99, 25, 5),
        ('Dambıl Seti', 999.99, 100, 5),
        ('Yoga Matı', 299.99, 150, 5),
        ('Bisiklet', 8999.99, 35, 5),
        ('Futbol Topu', 499.99, 200, 5)
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO urunler (urun_adi, fiyat, stok_miktari, kategori_id) 
        VALUES (?, ?, ?, ?)
    ''', urunler)
    
    # Müşterileri ekle
    musteriler = [
        ('Ahmet', 'Yılmaz', 'ahmet.yilmaz@email.com', 'İstanbul'),
        ('Fatma', 'Kaya', 'fatma.kaya@email.com', 'Ankara'),
        ('Mehmet', 'Demir', 'mehmet.demir@email.com', 'İzmir'),
        ('Ayşe', 'Çelik', 'ayse.celik@email.com', 'Bursa'),
        ('Ali', 'Şahin', 'ali.sahin@email.com', 'Antalya'),
        ('Zeynep', 'Arslan', 'zeynep.arslan@email.com', 'İstanbul'),
        ('Mustafa', 'Koç', 'mustafa.koc@email.com', 'Ankara'),
        ('Elif', 'Öztürk', 'elif.ozturk@email.com', 'İzmir'),
        ('Emre', 'Aydın', 'emre.aydin@email.com', 'Konya'),
        ('Selin', 'Yıldız', 'selin.yildiz@email.com', 'Adana'),
        ('Burak', 'Aksoy', 'burak.aksoy@email.com', 'Gaziantep'),
        ('Deniz', 'Korkmaz', 'deniz.korkmaz@email.com', 'Kayseri'),
        ('Can', 'Özdemir', 'can.ozdemir@email.com', 'Mersin'),
        ('İrem', 'Polat', 'irem.polat@email.com', 'Eskişehir'),
        ('Oğuz', 'Kılıç', 'oguz.kilic@email.com', 'Trabzon')
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO musteriler (ad, soyad, email, sehir) 
        VALUES (?, ?, ?, ?)
    ''', musteriler)
    
    # Satışları ekle (son 3 ayın verileri)
    random.seed(42)  # Tekrarlanabilirlik için
    
    satislar = []
    bugun = datetime.now()
    
    for _ in range(500):  # 500 adet satış kaydı
        urun_id = random.randint(1, 25)
        musteri_id = random.randint(1, 15)
        miktar = random.randint(1, 5)
        
        # Ürün fiyatını al
        cursor.execute('SELECT fiyat FROM urunler WHERE id = ?', (urun_id,))
        result = cursor.fetchone()
        if result is None:
            continue  # Ürün bulunamadıysa bu satışı atla
        fiyat = result[0]
        toplam_tutar = fiyat * miktar
        
        # Son 90 gün içinde rastgele bir tarih
        gun_oncesi = random.randint(0, 90)
        satis_tarihi = (bugun - timedelta(days=gun_oncesi)).strftime('%Y-%m-%d')
        
        satislar.append((urun_id, musteri_id, miktar, toplam_tutar, satis_tarihi))
    
    cursor.executemany('''
        INSERT INTO satislar (urun_id, musteri_id, miktar, toplam_tutar, satis_tarihi) 
        VALUES (?, ?, ?, ?, ?)
    ''', satislar)
    
    conn.commit()
    conn.close()
    
    print("Veritabanı başarıyla oluşturuldu: sales.db")
    print("Tablolar: kategoriler, urunler, musteriler, satislar")

def get_schema():
    """Veritabanı şemasını döndürür."""
    
    schema = """
Veritabanı Şeması:

1. kategoriler tablosu:
   - id: INTEGER (Birincil anahtar, otomatik artan)
   - kategori_adi: TEXT (Kategori adı - örn: Elektronik, Giyim, Kitap)

2. urunler tablosu:
   - id: INTEGER (Birincil anahtar, otomatik artan)
   - urun_adi: TEXT (Ürün adı)
   - fiyat: REAL (Ürün fiyatı TL cinsinden)
   - stok_miktari: INTEGER (Mevcut stok miktarı)
   - kategori_id: INTEGER (kategoriler tablosuna referans)

3. musteriler tablosu:
   - id: INTEGER (Birincil anahtar, otomatik artan)
   - ad: TEXT (Müşteri adı)
   - soyad: TEXT (Müşteri soyadı)
   - email: TEXT (E-posta adresi)
   - sehir: TEXT (Şehir - örn: İstanbul, Ankara, İzmir)

4. satislar tablosu:
   - id: INTEGER (Birincil anahtar, otomatik artan)
   - urun_id: INTEGER (urunler tablosuna referans)
   - musteri_id: INTEGER (musteriler tablosuna referans)
   - miktar: INTEGER (Satılan ürün adedi)
   - toplam_tutar: REAL (Toplam satış tutarı TL cinsinden)
   - satis_tarihi: DATE (Satış tarihi YYYY-MM-DD formatında)

İlişkiler:
- urunler.kategori_id -> kategoriler.id
- satislar.urun_id -> urunler.id
- satislar.musteri_id -> musteriler.id
"""
    return schema

if __name__ == '__main__':
    create_database()
    print("\n" + get_schema())
