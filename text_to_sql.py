"""
Doğal Dilden SQL Sorgusu Oluşturucu (Text-To-SQL)

Bu uygulama, Türkçe doğal dil sorgularını SQL sorgularına çevirir
ve sonuçları tablolar halinde gösterir.
"""

import os
import sys
import re
import sqlite3
from openai import OpenAI
from tabulate import tabulate
from dotenv import load_dotenv
from setup_database import get_schema, create_database

# .env dosyasından API anahtarını yükle
load_dotenv()


def get_openai_client():
    """OpenAI istemcisini oluşturur."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY bulunamadı. Lütfen .env dosyasına veya "
            "ortam değişkenlerine OPENAI_API_KEY ekleyin."
        )
    return OpenAI(api_key=api_key)


def generate_sql_query(client, user_query: str, schema: str) -> str:
    """
    Kullanıcının doğal dil sorgusunu SQL sorgusuna çevirir.
    
    Args:
        client: OpenAI istemcisi
        user_query: Türkçe doğal dil sorgusu
        schema: Veritabanı şeması
    
    Returns:
        SQL sorgusu
    """
    system_prompt = f"""Sen bir SQL uzmanısın. Sana verilen veritabanı şemasını kullanarak,
kullanıcının Türkçe doğal dil sorgusunu SQLite SQL sorgusuna çevirmelisin.

{schema}

Kurallar:
1. Sadece SELECT sorguları üret. INSERT, UPDATE, DELETE gibi değişiklik yapan sorgular üretme.
2. Sorgu sonucu olarak sadece SQL kodunu döndür, açıklama ekleme.
3. SQL kodunu ``` işaretleri olmadan düz metin olarak döndür.
4. Tarih karşılaştırmalarında SQLite'ın date() fonksiyonunu kullan.
5. "Geçen ay" ifadesi için son 30 gün, "bu ay" ifadesi için ayın başından bugüne kadar olan tarih aralığını kullan.
6. Türkçe karakterleri doğru şekilde işle."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0,
        max_tokens=500
    )
    
    sql_query = response.choices[0].message.content.strip()
    
    # SQL kod bloklarını temizle (```sql ... ``` gibi)
    if sql_query.startswith("```"):
        lines = sql_query.split("\n")
        sql_query = "\n".join(lines[1:-1])
    
    return sql_query


def execute_query(db_path: str, sql_query: str):
    """
    SQL sorgusunu çalıştırır ve sonuçları döndürür.
    
    Args:
        db_path: Veritabanı dosya yolu
        sql_query: Çalıştırılacak SQL sorgusu
    
    Returns:
        (sütun_adları, sonuçlar) tuple'ı
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql_query)
        columns = [description[0] for description in cursor.description]
        results = cursor.fetchall()
        return columns, results
    finally:
        conn.close()


def display_results(columns, results):
    """
    Sorgu sonuçlarını tablo formatında gösterir.
    
    Args:
        columns: Sütun adları listesi
        results: Sonuç satırları listesi
    """
    if not results:
        print("\nSonuç bulunamadı.")
        return
    
    print("\n" + tabulate(results, headers=columns, tablefmt="grid"))
    print(f"\nToplam {len(results)} kayıt bulundu.")


def validate_query(sql_query: str) -> bool:
    """
    SQL sorgusunun güvenli olup olmadığını kontrol eder.
    Sadece SELECT sorgularına izin verir.
    
    Args:
        sql_query: Kontrol edilecek SQL sorgusu
    
    Returns:
        True eğer sorgu güvenli ise
    """
    # Tehlikeli anahtar kelimeleri kontrol et
    dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 
                          'ALTER', 'TRUNCATE', 'EXEC', 'EXECUTE', 'ATTACH',
                          'DETACH', 'PRAGMA', 'VACUUM', 'REINDEX']
    
    upper_query = sql_query.upper()
    
    # Birden fazla statement kontrolü (SQL injection koruması)
    # Sorgu içinde noktalı virgül varsa ve SELECT dışında komut olabilir
    if ';' in sql_query:
        # Noktalı virgülden sonra boşluk dışında karakter varsa reddet
        parts = sql_query.split(';')
        for i, part in enumerate(parts[:-1]):  # Son parça hariç
            next_part = parts[i + 1].strip()
            if next_part and not next_part.startswith('--'):
                return False
    
    for keyword in dangerous_keywords:
        # Kelime sınırlarını kontrol et
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, upper_query):
            return False
    
    # SELECT ile başlamalı
    if not upper_query.strip().startswith('SELECT'):
        return False
    
    return True


def text_to_sql(user_query: str, db_path: str = 'sales.db'):
    """
    Ana fonksiyon: Doğal dil sorgusunu SQL'e çevirir ve çalıştırır.
    
    Args:
        user_query: Türkçe doğal dil sorgusu
        db_path: Veritabanı dosya yolu
    """
    print(f"\n{'='*60}")
    print(f"Soru: {user_query}")
    print('='*60)
    
    # OpenAI istemcisini oluştur
    client = get_openai_client()
    
    # Veritabanı şemasını al
    schema = get_schema()
    
    # SQL sorgusunu oluştur
    print("\nSQL sorgusu oluşturuluyor...")
    sql_query = generate_sql_query(client, user_query, schema)
    print(f"\nOluşturulan SQL:\n{sql_query}")
    
    # Sorguyu doğrula
    if not validate_query(sql_query):
        print("\nHATA: Güvenli olmayan sorgu tespit edildi. Sadece SELECT sorguları çalıştırılabilir.")
        return
    
    # Sorguyu çalıştır
    try:
        columns, results = execute_query(db_path, sql_query)
        display_results(columns, results)
    except sqlite3.Error as e:
        print(f"\nSQL Hatası: {e}")
    except Exception as e:
        print(f"\nHata: {e}")


def demo_mode():
    """
    Demo modu: Örnek Türkçe sorgularla sistemi gösterir.
    OPENAI_API_KEY gerektirmez.
    """
    print("\n" + "="*60)
    print("DEMO MODU - Text-to-SQL Örnek Gösterimi")
    print("="*60)
    
    # Örnek sorgular ve SQL karşılıkları
    demo_queries = [
        {
            "soru": "En çok satış yapan 5 ürünü listele",
            "sql": """SELECT u.urun_adi, SUM(s.miktar) as toplam_satis
FROM urunler u
JOIN satislar s ON u.id = s.urun_id
GROUP BY u.id, u.urun_adi
ORDER BY toplam_satis DESC
LIMIT 5"""
        },
        {
            "soru": "İstanbul'daki müşterileri göster",
            "sql": """SELECT ad, soyad, email, sehir
FROM musteriler
WHERE sehir = 'İstanbul'"""
        },
        {
            "soru": "Elektronik kategorisindeki ürünleri fiyata göre sırala",
            "sql": """SELECT u.urun_adi, u.fiyat, u.stok_miktari
FROM urunler u
JOIN kategoriler k ON u.kategori_id = k.id
WHERE k.kategori_adi = 'Elektronik'
ORDER BY u.fiyat DESC"""
        },
        {
            "soru": "Her kategoride kaç ürün var?",
            "sql": """SELECT k.kategori_adi, COUNT(u.id) as urun_sayisi
FROM kategoriler k
LEFT JOIN urunler u ON k.id = u.kategori_id
GROUP BY k.id, k.kategori_adi
ORDER BY urun_sayisi DESC"""
        },
        {
            "soru": "Toplam satış tutarı en yüksek 3 müşteriyi bul",
            "sql": """SELECT m.ad, m.soyad, m.sehir, SUM(s.toplam_tutar) as toplam_harcama
FROM musteriler m
JOIN satislar s ON m.id = s.musteri_id
GROUP BY m.id, m.ad, m.soyad, m.sehir
ORDER BY toplam_harcama DESC
LIMIT 3"""
        }
    ]
    
    db_path = 'sales.db'
    
    for demo in demo_queries:
        print(f"\n{'='*60}")
        print(f"Türkçe Soru: {demo['soru']}")
        print('='*60)
        print(f"\nOluşturulan SQL:\n{demo['sql']}")
        
        try:
            columns, results = execute_query(db_path, demo['sql'])
            display_results(columns, results)
        except sqlite3.Error as e:
            print(f"\nSQL Hatası: {e}")
        
        print("\n" + "-"*60)


def interactive_mode():
    """
    Etkileşimli mod: Kullanıcıdan sorgular alır ve sonuçları gösterir.
    """
    print("\n" + "="*60)
    print("Text-to-SQL - Etkileşimli Mod")
    print("="*60)
    print("\nTürkçe sorularınızı yazın. Çıkmak için 'q' veya 'çıkış' yazın.")
    print("Örnek: 'En çok satış yapan 5 ürünü listele'")
    
    while True:
        try:
            user_input = input("\nSorunuz: ").strip()
            
            if user_input.lower() in ['q', 'quit', 'exit', 'çıkış', 'çık']:
                print("\nGüle güle!")
                break
            
            if not user_input:
                continue
            
            text_to_sql(user_input)
            
        except KeyboardInterrupt:
            print("\n\nGüle güle!")
            break


def main():
    """Ana giriş noktası."""
    # Veritabanını kontrol et, yoksa oluştur
    if not os.path.exists('sales.db'):
        print("Veritabanı bulunamadı, oluşturuluyor...")
        create_database()
    
    # Komut satırı argümanlarını kontrol et
    if len(sys.argv) > 1:
        if sys.argv[1] == '--demo':
            demo_mode()
        elif sys.argv[1] == '--interactive':
            interactive_mode()
        else:
            # Tek sorguluk mod
            query = ' '.join(sys.argv[1:])
            text_to_sql(query)
    else:
        # Varsayılan olarak demo modunu çalıştır
        print("Kullanım:")
        print("  python text_to_sql.py --demo          # Demo modunu çalıştır")
        print("  python text_to_sql.py --interactive   # Etkileşimli mod")
        print("  python text_to_sql.py <sorgu>         # Tek sorgu çalıştır")
        print("\nDemo modu çalıştırılıyor...")
        demo_mode()


if __name__ == '__main__':
    main()
