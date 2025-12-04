import os
import sqlite3
import pandas as pd
import streamlit as st
import google.generativeai as genai

# --- Sayfa Yapılandırması ---
st.set_page_config(
    page_title="Text-to-SQL & CRUD Uygulaması",
    page_icon="🔍",
    layout="wide"
)

# --- CSS Stilleri ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sql-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: monospace;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .crud-header {
        font-size: 1.5rem;
        color: #43A047;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Veritabanı Ayarları ---
DB_FILE = 'sales.db'

@st.cache_resource
def init_database():
    """Veritabanını oluştur ve örnek verilerle doldur"""
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
    
    conn.commit()
    conn.close()
    return True

@st.cache_resource
def init_model(api_key):
    """Gemini modelini başlat"""
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
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=schema_prompt)
    return model

def get_sql_query(model, user_query):
    """Doğal dilden SQL sorgusu oluştur"""
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
        st.error(f"SQL sorgusu oluşturulurken hata: {e}")
        return None

def execute_sql_query(sql_query):
    """SQL sorgusunu çalıştır"""
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"SQL sorgusu yürütülürken hata: {e}")
        return None

# --- CRUD İşlemleri ---
def add_product(product_name, category, price):
    """Yeni ürün ekle"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (product_name, category, price) VALUES (?, ?, ?)",
            (product_name, category, price)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Ürün eklenirken hata: {e}")
        return False

def update_product(product_id, product_name, category, price):
    """Ürün güncelle"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE products SET product_name = ?, category = ?, price = ? WHERE product_id = ?",
            (product_name, category, price, product_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Ürün güncellenirken hata: {e}")
        return False

def delete_product(product_id):
    """Ürün sil"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Ürün silinirken hata: {e}")
        return False

def add_sale(product_id, customer_id, sale_date, quantity, total_amount):
    """Yeni satış ekle"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sales (product_id, customer_id, sale_date, quantity, total_amount) VALUES (?, ?, ?, ?, ?)",
            (product_id, customer_id, sale_date, quantity, total_amount)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Satış eklenirken hata: {e}")
        return False

def update_sale(sale_id, product_id, customer_id, sale_date, quantity, total_amount):
    """Satış güncelle"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sales SET product_id = ?, customer_id = ?, sale_date = ?, quantity = ?, total_amount = ? WHERE sale_id = ?",
            (product_id, customer_id, sale_date, quantity, total_amount, sale_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Satış güncellenirken hata: {e}")
        return False

def delete_sale(sale_id):
    """Satış sil"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sales WHERE sale_id = ?", (sale_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Satış silinirken hata: {e}")
        return False

def get_product_by_id(product_id):
    """ID'ye göre ürün getir"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        return None

def get_sale_by_id(sale_id):
    """ID'ye göre satış getir"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sales WHERE sale_id = ?", (sale_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        return None

# --- Ana Uygulama ---
def main():
    # Başlık
    st.markdown('<h1 class="main-header">🔍 Text-to-SQL & CRUD Uygulaması</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Veritabanını başlat
    init_database()
    
    # Sidebar - API Anahtarı ve Ayarlar
    with st.sidebar:
        st.header("⚙️ Ayarlar")
        
        # API Anahtarı
        api_key = st.text_input(
            "Google API Anahtarı",
            type="password",
            value=os.environ.get("GOOGLE_API_KEY", ""),
            help="Google AI Studio'dan alınan API anahtarınızı girin"
        )
        
        st.markdown("---")
        
        # Veritabanı Şeması
        st.header("📊 Veritabanı Şeması")
        st.code("""
TABLE products:
- product_id (INTEGER, PK)
- product_name (TEXT)
- category (TEXT)
- price (REAL)

TABLE sales:
- sale_id (INTEGER, PK)
- product_id (INTEGER, FK)
- customer_id (INTEGER)
- sale_date (TEXT)
- quantity (INTEGER)
- total_amount (REAL)
        """, language="sql")
        
        st.markdown("---")
        
        # Örnek Sorgular
        st.header("💡 Örnek Sorgular")
        example_queries = [
            "Tüm ürünleri listele",
            "En pahalı 3 ürünü göster",
            "Toplam satış miktarını hesapla",
            "Kategori bazında ürün sayısını göster",
            "En çok satan 5 ürünü listele",
            "Temmuz ayındaki satışları göster"
        ]
        for query in example_queries:
            st.markdown(f"• {query}")
    
    # Ana Sekmeler
    main_tab1, main_tab2, main_tab3 = st.tabs(["🤖 AI Sorgu", "📦 Ürün Yönetimi", "💰 Satış Yönetimi"])
    
    # --- TAB 1: AI Sorgu (Text-to-SQL) ---
    with main_tab1:
        st.header("🤖 Yapay Zeka ile Doğal Dil Sorgusu")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📝 Sorgunuzu Yazın")
            
            # Kullanıcı Girişi
            user_query = st.text_area(
                "Doğal dilde sorgunuzu yazın:",
                placeholder="Örnek: En çok satan 5 ürünü listele",
                height=100,
                key="ai_query"
            )
            
            # Butonlar
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                generate_btn = st.button("🚀 SQL Oluştur", type="primary", use_container_width=True)
            with col_btn2:
                clear_btn = st.button("🗑️ Temizle", use_container_width=True)
            
            if clear_btn:
                st.rerun()
        
        with col2:
            st.subheader("📊 Mevcut Veriler Önizleme")
            
            preview_tab1, preview_tab2 = st.tabs(["Ürünler", "Satışlar"])
            
            with preview_tab1:
                products_df = execute_sql_query("SELECT * FROM products LIMIT 5")
                if products_df is not None:
                    st.dataframe(products_df, use_container_width=True, height=200)
            
            with preview_tab2:
                sales_df = execute_sql_query("SELECT * FROM sales LIMIT 5")
                if sales_df is not None:
                    st.dataframe(sales_df, use_container_width=True, height=200)
        
        # Sonuçlar
        if generate_btn and user_query:
            if not api_key:
                st.warning("⚠️ Lütfen sidebar'dan API anahtarınızı girin!")
            else:
                with st.spinner("SQL sorgusu oluşturuluyor..."):
                    try:
                        model = init_model(api_key)
                        generated_sql = get_sql_query(model, user_query)
                        
                        if generated_sql:
                            st.subheader("🔧 Oluşturulan SQL Sorgusu")
                            st.code(generated_sql, language="sql")
                            
                            # Sorguyu çalıştır
                            st.subheader("📋 Sorgu Sonuçları")
                            with st.spinner("Sorgu çalıştırılıyor..."):
                                results_df = execute_sql_query(generated_sql)
                                
                                if results_df is not None:
                                    st.success(f"✅ {len(results_df)} satır bulundu")
                                    st.dataframe(results_df, use_container_width=True)
                                    
                                    # CSV İndirme
                                    csv = results_df.to_csv(index=False).encode('utf-8')
                                    st.download_button(
                                        label="📥 CSV olarak indir",
                                        data=csv,
                                        file_name="sorgu_sonuclari.csv",
                                        mime="text/csv"
                                    )
                                else:
                                    st.error("Sorgu çalıştırılırken bir hata oluştu.")
                    except Exception as e:
                        st.error(f"Hata: {e}")
    
    # --- TAB 2: Ürün Yönetimi (CRUD) ---
    with main_tab2:
        st.header("📦 Ürün Yönetimi")
        
        # Ürün Listesi
        st.subheader("📋 Ürün Listesi")
        products_df = execute_sql_query("SELECT * FROM products ORDER BY product_id")
        if products_df is not None:
            st.dataframe(products_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # CRUD İşlemleri
        crud_tab1, crud_tab2, crud_tab3 = st.tabs(["➕ Yeni Ürün Ekle", "✏️ Ürün Güncelle", "🗑️ Ürün Sil"])
        
        # Yeni Ürün Ekle
        with crud_tab1:
            st.subheader("➕ Yeni Ürün Ekle")
            with st.form("add_product_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_product_name = st.text_input("Ürün Adı", placeholder="Örn: Tablet")
                with col2:
                    new_category = st.selectbox(
                        "Kategori",
                        ["Electronics", "Furniture", "Kitchenware", "Stationery", "Other"]
                    )
                with col3:
                    new_price = st.number_input("Fiyat (₺)", min_value=0.0, step=0.01, format="%.2f")
                
                submit_add = st.form_submit_button("➕ Ürün Ekle", type="primary", use_container_width=True)
                
                if submit_add:
                    if new_product_name and new_price > 0:
                        if add_product(new_product_name, new_category, new_price):
                            st.success(f"✅ '{new_product_name}' başarıyla eklendi!")
                            st.rerun()
                    else:
                        st.warning("⚠️ Lütfen tüm alanları doldurun!")
        
        # Ürün Güncelle
        with crud_tab2:
            st.subheader("✏️ Ürün Güncelle")
            
            # Ürün seçimi
            if products_df is not None and len(products_df) > 0:
                product_options = {f"{row['product_id']} - {row['product_name']}": row['product_id'] 
                                   for _, row in products_df.iterrows()}
                selected_product = st.selectbox(
                    "Güncellenecek Ürünü Seçin",
                    options=list(product_options.keys()),
                    key="update_product_select"
                )
                
                if selected_product:
                    product_id = product_options[selected_product]
                    product_data = get_product_by_id(product_id)
                    
                    if product_data:
                        with st.form("update_product_form"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                upd_product_name = st.text_input("Ürün Adı", value=product_data[1])
                            with col2:
                                categories = ["Electronics", "Furniture", "Kitchenware", "Stationery", "Other"]
                                current_cat_idx = categories.index(product_data[2]) if product_data[2] in categories else 0
                                upd_category = st.selectbox("Kategori", categories, index=current_cat_idx)
                            with col3:
                                upd_price = st.number_input("Fiyat (₺)", value=float(product_data[3]), min_value=0.0, step=0.01, format="%.2f")
                            
                            submit_update = st.form_submit_button("✏️ Güncelle", type="primary", use_container_width=True)
                            
                            if submit_update:
                                if update_product(product_id, upd_product_name, upd_category, upd_price):
                                    st.success(f"✅ Ürün başarıyla güncellendi!")
                                    st.rerun()
            else:
                st.info("Güncellenecek ürün bulunamadı.")
        
        # Ürün Sil
        with crud_tab3:
            st.subheader("🗑️ Ürün Sil")
            
            if products_df is not None and len(products_df) > 0:
                product_options = {f"{row['product_id']} - {row['product_name']}": row['product_id'] 
                                   for _, row in products_df.iterrows()}
                selected_delete_product = st.selectbox(
                    "Silinecek Ürünü Seçin",
                    options=list(product_options.keys()),
                    key="delete_product_select"
                )
                
                if selected_delete_product:
                    product_id = product_options[selected_delete_product]
                    
                    st.warning(f"⚠️ '{selected_delete_product}' ürününü silmek istediğinizden emin misiniz?")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Evet, Sil", type="primary", use_container_width=True):
                            if delete_product(product_id):
                                st.success("✅ Ürün başarıyla silindi!")
                                st.rerun()
                    with col2:
                        if st.button("❌ İptal", use_container_width=True):
                            st.rerun()
            else:
                st.info("Silinecek ürün bulunamadı.")
    
    # --- TAB 3: Satış Yönetimi (CRUD) ---
    with main_tab3:
        st.header("💰 Satış Yönetimi")
        
        # Satış Listesi
        st.subheader("📋 Satış Listesi")
        sales_query = """
            SELECT s.sale_id, p.product_name, s.customer_id, s.sale_date, s.quantity, s.total_amount
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            ORDER BY s.sale_id
        """
        sales_df = execute_sql_query(sales_query)
        if sales_df is not None:
            st.dataframe(sales_df, use_container_width=True, hide_index=True)
        
        # Raw sales data for CRUD operations
        raw_sales_df = execute_sql_query("SELECT * FROM sales ORDER BY sale_id")
        
        st.markdown("---")
        
        # CRUD İşlemleri
        sale_crud_tab1, sale_crud_tab2, sale_crud_tab3 = st.tabs(["➕ Yeni Satış Ekle", "✏️ Satış Güncelle", "🗑️ Satış Sil"])
        
        # Yeni Satış Ekle
        with sale_crud_tab1:
            st.subheader("➕ Yeni Satış Ekle")
            
            # Ürün listesini al
            products_for_sale = execute_sql_query("SELECT product_id, product_name, price FROM products")
            
            if products_for_sale is not None and len(products_for_sale) > 0:
                with st.form("add_sale_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        product_options_sale = {f"{row['product_name']} (₺{row['price']})": (row['product_id'], row['price']) 
                                                for _, row in products_for_sale.iterrows()}
                        selected_sale_product = st.selectbox(
                            "Ürün Seçin",
                            options=list(product_options_sale.keys())
                        )
                        new_customer_id = st.number_input("Müşteri ID", min_value=1, step=1, value=101)
                    
                    with col2:
                        new_sale_date = st.date_input("Satış Tarihi")
                        new_quantity = st.number_input("Adet", min_value=1, step=1, value=1)
                    
                    # Toplam tutarı hesapla
                    if selected_sale_product:
                        product_id, unit_price = product_options_sale[selected_sale_product]
                        calculated_total = unit_price * new_quantity
                        st.info(f"💵 Toplam Tutar: ₺{calculated_total:.2f}")
                    
                    submit_add_sale = st.form_submit_button("➕ Satış Ekle", type="primary", use_container_width=True)
                    
                    if submit_add_sale:
                        product_id, unit_price = product_options_sale[selected_sale_product]
                        total_amount = unit_price * new_quantity
                        sale_date_str = new_sale_date.strftime("%Y-%m-%d")
                        
                        if add_sale(product_id, new_customer_id, sale_date_str, new_quantity, total_amount):
                            st.success("✅ Satış başarıyla eklendi!")
                            st.rerun()
            else:
                st.warning("⚠️ Önce ürün eklemeniz gerekiyor!")
        
        # Satış Güncelle
        with sale_crud_tab2:
            st.subheader("✏️ Satış Güncelle")
            
            if raw_sales_df is not None and len(raw_sales_df) > 0 and products_for_sale is not None:
                sale_options = {f"Satış #{row['sale_id']} - Müşteri {row['customer_id']} ({row['sale_date']})": row['sale_id'] 
                               for _, row in raw_sales_df.iterrows()}
                selected_sale = st.selectbox(
                    "Güncellenecek Satışı Seçin",
                    options=list(sale_options.keys()),
                    key="update_sale_select"
                )
                
                if selected_sale:
                    sale_id = sale_options[selected_sale]
                    sale_data = get_sale_by_id(sale_id)
                    
                    if sale_data:
                        with st.form("update_sale_form"):
                            col1, col2 = st.columns(2)
                            
                            product_list = [(row['product_id'], row['product_name'], row['price']) 
                                           for _, row in products_for_sale.iterrows()]
                            product_names = [f"{p[1]} (₺{p[2]})" for p in product_list]
                            current_product_idx = next((i for i, p in enumerate(product_list) if p[0] == sale_data[1]), 0)
                            
                            with col1:
                                upd_product = st.selectbox("Ürün", product_names, index=current_product_idx)
                                upd_customer_id = st.number_input("Müşteri ID", value=sale_data[2], min_value=1, step=1)
                            
                            with col2:
                                from datetime import datetime
                                current_date = datetime.strptime(sale_data[3], "%Y-%m-%d").date()
                                upd_sale_date = st.date_input("Satış Tarihi", value=current_date)
                                upd_quantity = st.number_input("Adet", value=sale_data[4], min_value=1, step=1)
                            
                            # Toplam tutarı hesapla
                            selected_idx = product_names.index(upd_product)
                            new_unit_price = product_list[selected_idx][2]
                            new_total = new_unit_price * upd_quantity
                            st.info(f"💵 Yeni Toplam Tutar: ₺{new_total:.2f}")
                            
                            submit_update_sale = st.form_submit_button("✏️ Güncelle", type="primary", use_container_width=True)
                            
                            if submit_update_sale:
                                new_product_id = product_list[selected_idx][0]
                                sale_date_str = upd_sale_date.strftime("%Y-%m-%d")
                                
                                if update_sale(sale_id, new_product_id, upd_customer_id, sale_date_str, upd_quantity, new_total):
                                    st.success("✅ Satış başarıyla güncellendi!")
                                    st.rerun()
            else:
                st.info("Güncellenecek satış bulunamadı.")
        
        # Satış Sil
        with sale_crud_tab3:
            st.subheader("🗑️ Satış Sil")
            
            if raw_sales_df is not None and len(raw_sales_df) > 0:
                sale_options = {f"Satış #{row['sale_id']} - Müşteri {row['customer_id']} ({row['sale_date']}) - ₺{row['total_amount']}": row['sale_id'] 
                               for _, row in raw_sales_df.iterrows()}
                selected_delete_sale = st.selectbox(
                    "Silinecek Satışı Seçin",
                    options=list(sale_options.keys()),
                    key="delete_sale_select"
                )
                
                if selected_delete_sale:
                    sale_id = sale_options[selected_delete_sale]
                    
                    st.warning(f"⚠️ '{selected_delete_sale}' satışını silmek istediğinizden emin misiniz?")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Evet, Sil", type="primary", use_container_width=True, key="confirm_delete_sale"):
                            if delete_sale(sale_id):
                                st.success("✅ Satış başarıyla silindi!")
                                st.rerun()
                    with col2:
                        if st.button("❌ İptal", use_container_width=True, key="cancel_delete_sale"):
                            st.rerun()
            else:
                st.info("Silinecek satış bulunamadı.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: gray;">
            <p>🤖 Google Gemini AI ile desteklenmektedir | 📊 SQLite Veritabanı</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()