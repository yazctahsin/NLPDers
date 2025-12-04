import os
import sqlite3
import pandas as pd
import google.generativeai as genai

# --- 1. API Anahtarını Yapılandırma ---
API_KEY = os.environ.get("GOOGLE_API_KEY")

# API anahtarını burada doğrudan ayarlayabilirsiniz:
# API_KEY = "YOUR_ACTUAL_API_KEY"

API_CONFIGURED = False
if not API_KEY:
    print("HATA: GOOGLE_API_KEY ortam değişkeni bulunamadı.")
    print("Lütfen API anahtarınızı ayarlayın:")
    print("  Windows: set GOOGLE_API_KEY=your_api_key")
    print("  Veya kodda API_KEY değişkenine doğrudan yazın.")
else:
    genai.configure(api_key=API_KEY)
    print("Google Generative AI API başarıyla yapılandırıldı.")
    API_CONFIGURED = True

# --- 2. SQLite Veritabanı ve Örnek Veri Oluşturma ---
DB_FILE = 'sales.db'

def create_and_populate_database():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Tabloları oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                category TEXT,
                price REAL NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                sale_date TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );
        """)
        print("Tablolar 'products' ve 'sales' oluşturuldu veya zaten mevcut.")

        # Ürün verilerini ekle
        cursor.execute("SELECT COUNT(*) FROM products;")
        if cursor.fetchone()[0] == 0:
            products_data = [
                ('Laptop', 'Electronics', 1200.00),
                ('Mouse', 'Electronics', 25.00),
                ('Keyboard', 'Electronics', 75.00),
                ('Monitor', 'Electronics', 300.00),
                ('Desk Chair', 'Furniture', 150.00),
                ('Coffee Mug', 'Kitchenware', 10.00),
                ('Notebook', 'Stationery', 5.00),
                ('Pen Set', 'Stationery', 12.00)
            ]
            cursor.executemany(
                "INSERT INTO products (product_name, category, price) VALUES (?, ?, ?)",
                products_data
            )
            print("Örnek ürün verileri eklendi.")

        # Satış verilerini ekle
        cursor.execute("SELECT COUNT(*) FROM sales;")
        if cursor.fetchone()[0] == 0:
            sales_data = [
                (1, 101, '2024-06-15', 1, 1200.00),
                (2, 102, '2024-06-16', 2, 50.00),
                (1, 103, '2024-07-01', 1, 1200.00),
                (3, 101, '2024-07-02', 1, 75.00),
                (4, 104, '2024-07-05', 1, 300.00),
                (5, 105, '2024-07-08', 1, 150.00),
                (6, 102, '2024-07-10', 3, 30.00),
                (7, 101, '2024-07-12', 5, 25.00),
                (8, 103, '2024-08-01', 1, 12.00),
                (1, 104, '2024-08-03', 1, 1200.00),
                (2, 105, '2024-08-05', 1, 25.00)
            ]
            cursor.executemany(
                "INSERT INTO sales (product_id, customer_id, sale_date, quantity, total_amount) VALUES (?, ?, ?, ?, ?)",
                sales_data
            )
            print("Örnek satış verileri eklendi.")

        conn.commit()
        print("Veritabanı işlemleri tamamlandı.")
    except sqlite3.Error as e:
        print(f"Veritabanı hatası: {e}")
    finally:
        if conn:
            conn.close()

create_and_populate_database()

# --- 3. LLM için Veritabanı Şeması Tanıtımı (System Prompt) ---
schema_prompt = """
Aşağıdaki SQLite veritabanı şemasına göre SQL sorguları oluşturmanız istenmektedir:

TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    category TEXT,
    price REAL NOT NULL
);

TABLE sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    sale_date TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

Yalnızca verilen şemaya uygun SQL sorguları oluşturun. Açıklama veya başka bir metin eklemeyin.
Sadece SQL sorgusunu döndürün.
"""

# --- 4. Generative Model'i Başlatma ---
model = None
if API_CONFIGURED:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=schema_prompt)
        print("Generative Model 'gemini-1.5-flash' başlatıldı.")
    except Exception as e:
        print(f"Model başlatılırken hata: {e}")
else:
    print("API anahtarı bulunamadığı için Generative Model başlatılamadı.")

# --- 5. Doğal Dilden SQL'e Çevirme Fonksiyonu Geliştirme ---
def get_sql_query(user_query):
    if model is None:
        print("Hata: Model başlatılamadı.")
        return None
    try:
        response = model.generate_content(user_query)
        sql_response_text = response.text.strip()

        # Markdown kod bloğu işaretlerini kaldır
        if sql_response_text.startswith('```sql'):
            sql_response_text = sql_response_text[6:]
        elif sql_response_text.startswith('```sqlite'):
            sql_response_text = sql_response_text[9:]
        elif sql_response_text.startswith('```'):
            sql_response_text = sql_response_text[3:]

        if sql_response_text.endswith('```'):
            sql_response_text = sql_response_text[:-3]

        return sql_response_text.strip()

    except Exception as e:
        print(f"SQL sorgusu oluşturulurken hata: {e}")
        return None

# --- 6. SQL Sorgusunu Çalıştırma ve Sonuçları Gösterme ---
def execute_sql_query(sql_query):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(sql_query, conn)
        return df
    except Exception as e:
        print(f"SQL sorgusu yürütülürken hata: {e}")
        return None
    finally:
        if conn:
            conn.close()

# --- 7. Örnek Sorgu ve Demo ---
if __name__ == "__main__":
    print("\n--- Text-to-SQL Demo Başlıyor ---\n")

    if not API_CONFIGURED:
        print("API anahtarı yapılandırılmadı. Veritabanını test sorgusuyla test ediyorum:\n")
        test_query = """
            SELECT p.product_name, SUM(s.quantity) as total_sold 
            FROM products p 
            JOIN sales s ON p.product_id = s.product_id 
            GROUP BY p.product_id 
            ORDER BY total_sold DESC 
            LIMIT 5;
        """
        print(f"Test SQL: {test_query}")
        results_df = execute_sql_query(test_query)
        if results_df is not None:
            print("\nSonuçlar:")
            print(results_df)
    else:
        user_natural_language_query = 'Geçen ay en çok satış yapan 5 ürünü listele'
        print(f"Doğal Dil Sorgusu: {user_natural_language_query}")

        generated_sql_query = get_sql_query(user_natural_language_query)

        if generated_sql_query:
            print(f"\nOluşturulan SQL Sorgusu:\n{generated_sql_query}\n")
            results_df = execute_sql_query(generated_sql_query)
            if results_df is not None:
                print("SQL Sorgu Sonuçları:")
                print(results_df)
        else:
            print("SQL sorgusu oluşturulamadı.")

    print("\n--- Text-to-SQL Demo Tamamlandı ---")