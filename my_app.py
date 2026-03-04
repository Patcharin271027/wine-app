import streamlit as st
import sqlite3
import pandas as pd
import io
from datetime import datetime, date

# 1. ตั้งค่าหน้าจอ
st.set_page_config(layout="wide", page_title="ระบบจัดการยอดขาย WINE")

# 2. เชื่อมต่อฐานข้อมูล (ใช้ชื่อไฟล์ใหม่เพื่อความชัวร์)
conn = sqlite3.connect('hotel_sales_final_v9.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS config_hotels (id INTEGER PRIMARY KEY, name TEXT UNIQUE)')
c.execute('CREATE TABLE IF NOT EXISTS config_suppliers (id INTEGER PRIMARY KEY, name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS sales_data 
             (id INTEGER PRIMARY KEY, supplier TEXT, stype TEXT, hotel TEXT, sale_date DATE, amount REAL)''')
conn.commit()

st.title("🏨 ระบบจัดการยอดขาย Wine")

# --- แถบด้านซ้าย (Sidebar): ส่วนตั้งค่าโรงแรมและร้านค้า ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบ")
    with st.expander("🏢 เพิ่ม/ลบ รายชื่อโรงแรม"):
        new_h = st.text_input("ชื่อโรงแรมใหม่", key="sidebar_new_h")
        if st.button("บันทึกโรงแรม"):
            if new_h:
                try:
                    c.execute("INSERT INTO config_hotels (name) VALUES (?)", (new_h.strip(),))
                    conn.commit()
                    st.rerun()
                except: st.warning("มีชื่อนี้อยู่แล้ว")
        h_data = pd.read_sql_query("SELECT name FROM config_hotels", conn)
        st.dataframe(h_data, hide_index=True)
        h_to_del = st.selectbox("เลือกโรงแรมที่จะลบ", [""] + h_data['name'].tolist(), key="sidebar_del_h")
        if st.button("ลบโรงแรม"):
            c.execute("DELETE FROM config_hotels WHERE name=?", (h_to_del,))
            conn.commit()
            st.rerun()

    with st.expander("🛍️ เพิ่ม/ลบ รายชื่อร้านค้า"):
        new_s = st.text_input("ชื่อร้านค้าใหม่", key="sidebar_new_s")
        if st.button("บันทึกร้านค้า"):
            if new_s:
                try:
                    c.execute("INSERT INTO config_suppliers (name) VALUES (?)", (new_s.strip(),))
                    conn.commit()
                    st.rerun()
                except: st.warning("มีชื่อนี้อยู่แล้ว")
        s_data = pd.read_sql_query("SELECT name FROM config_suppliers", conn)
        st.dataframe(s_data, hide_index=True)
        s_to_del = st.selectbox("เลือกร้านค้าที่จะลบ", [""] + s_data['name'].tolist(), key="sidebar_del_s")
        if st.button("ลบร้านค้า"):
            c.execute("DELETE FROM config_suppliers WHERE name=?", (s_to_del,))
            conn.commit()
            st.rerun()

# --- ส่วนที่ 1: ฟอร์มบันทึกยอดขาย (แก้ไขเพื่อให้บันทึกได้จริง) ---
st.subheader("📥 บันทึกยอดขาย WINE")
hotels_options = h_data['name'].tolist()
suppliers_options = s_data['name'].tolist()

if not hotels_options or not suppliers_options:
    st.info("💡 กรุณาเพิ่มรายชื่อ 'โรงแรม' และ 'ร้านค้า' ที่แถบด้านซ้ายมือก่อนนะคะ")
else:
    # การใช้ st.form(clear_on_submit=True) จะช่วยเคลียร์ค่าหลังกดบันทึก
    with st.form("main_sales_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        supplier_val = col1.selectbox("เลือก Supplier", suppliers_options)
        stype_val = col1.radio("ประเภทการขาย", ["CONSIGNMENT", "CREDIT"], horizontal=True)
        hotel_val = col2.selectbox("เลือกโรงแรม", hotels_options)
        sale_date_val = col2.date_input("เลือกวันที่ขาย", date.today())
        amount_val = st.number_input("ยอดเงินยอดขาย (บาท)", min_value=0.0, step=1.0)
        
        btn_save = st.form_submit_button("บันทึกข้อมูล")
        
        if btn_save:
            if amount_val > 0:
                # ทำการบันทึกข้อมูลลง Database
                c.execute("INSERT INTO sales_data (supplier, stype, hotel, sale_date, amount) VALUES (?,?,?,?,?)",
                          (supplier_val, stype_val, hotel_val, sale_date_val.strftime('%Y-%m-%d'), amount_val))
                conn.commit()
                st.success(f"✅ บันทึกยอด {amount_val:,.2f} บาท เรียบร้อยแล้ว!")
                # ใช้ st.rerun() เพื่ออัปเดตตารางสรุปทันที
                st.rerun()
            else:
                st.error("❌ กรุณาใส่ยอดเงินที่มากกว่า 0")

# --- ส่วนที่ 2: รายงานและการกรองข้อมูล (แยกวันที่เริ่มต้น - สิ้นสุด) ---
st.divider()
st.subheader("📊 รายงานสรุปยอดขาย WINE")

df_raw = pd.read_sql_query("SELECT * FROM sales_data", conn)

if not df_raw.empty:
    df_raw['sale_date'] = pd.to_datetime(df_raw['sale_date'])
    
    with st.container(border=True):
        st.write("🔍 ตัวกรองรายงาน")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        
        # ฟิลเตอร์กรองข้อมูล
        f_sup = f_col1.multiselect("Supplier", suppliers_options, default=suppliers_options)
        f_type = f_col2.multiselect("Type", ["CONSIGNMENT", "CREDIT"], default=["CONSIGNMENT", "CREDIT"])
        
        # ปรับปรุง: แยกฟิลด์วันที่เริ่มต้นและวันที่สิ้นสุดตามต้องการ
        start_filter = f_col3.date_input("วันที่เริ่มต้น", date.today().replace(day=1))
        end_filter = f_col4.date_input("วันที่สิ้นสุด", date.today())

    # กรองข้อมูลตามเงื่อนไข
    mask = (df_raw['supplier'].isin(f_sup)) & \
           (df_raw['stype'].isin(f_type)) & \
           (df_raw['sale_date'].dt.date >= start_filter) & \
           (df_raw['sale_date'].dt.date <= end_filter)
    
    df_filtered = df_raw.loc[mask].copy()

    if not df_filtered.empty:
        df_filtered['month_year'] = df_filtered['sale_date'].dt.strftime('%b-%y')
        pivot = df_filtered.pivot_table(index=['supplier', 'stype', 'hotel'], 
                                        columns='month_year', values='amount', 
                                        aggfunc='sum', fill_value=0, margins=True, margins_name='TOTAL')
        st.dataframe(pivot, use_container_width=True)
        
        # ปุ่มดาวน์โหลด Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            pivot.to_excel(writer, sheet_name='Monthly_Report')
        st.download_button("💾 ดาวน์โหลดรายงาน Excel", data=buffer, file_name="hotel_sales_report.xlsx")
        
        # --- ส่วนที่ 3: ระบบแก้ไข/ลบข้อมูล ---
        st.write("---")
        st.write("✏️ **จัดการข้อมูลที่บันทึกผิด**")
        with st.expander("แสดงรายการข้อมูลดิบเพื่อ แก้ไข หรือ ลบ"):
            manage_df = df_filtered[['id', 'supplier', 'stype', 'hotel', 'sale_date', 'amount']].copy()
            manage_df['sale_date'] = manage_df['sale_date'].dt.date
            st.dataframe(manage_df, hide_index=True)
            
            m_col1, m_col2, m_col3 = st.columns([1,2,1])
            target_id = m_col1.number_input("ระบุ ID ที่ต้องการจัดการ", min_value=1, step=1)
            edit_amount = m_col2.number_input("ระบุยอดเงินใหม่ (สำหรับแก้ไข)", min_value=0.0)
            
            if m_col3.button("🔄 อัปเดตยอดเงิน"):
                c.execute("UPDATE sales_data SET amount=? WHERE id=?", (edit_amount, target_id))
                conn.commit()
                st.success(f"อัปเดต ID {target_id} สำเร็จ!")
                st.rerun()
                
            if m_col3.button("🗑️ ลบข้อมูล"):
                c.execute("DELETE FROM sales_data WHERE id=?", (target_id,))
                conn.commit()
                st.warning(f"ลบข้อมูล ID {target_id} เรียบร้อย!")
                st.rerun()
    else:
        st.warning("⚠️ ไม่พบข้อมูลในช่วงเวลาที่เลือก")
else:
    st.info("ยังไม่มีข้อมูลในระบบ เริ่มบันทึกข้อมูลด้านบนได้เลยค่ะ")

conn.close()
# --- ส่วนที่ 4: ระบบสำรองฐานข้อมูล (เพิ่มเข้าไปท้ายไฟล์) ---
st.divider()
st.subheader("💾 ระบบสำรองและกู้คืนข้อมูล")
with st.expander("คลิกเพื่อดาวน์โหลดไฟล์ฐานข้อมูล (.db) หรืออัปโหลดกลับ"):
    # ต้องสะกดชื่อไฟล์ให้ตรงกับที่ตั้งไว้ในบรรทัดที่ 11 ของโค้ดคุณ
    db_filename = 'hotel_sales_final_v9.db' 
    
    # 1. ปุ่มสำหรับดาวน์โหลดไฟล์จากออนไลน์มาเก็บในเครื่อง
    try:
        with open(db_filename, 'rb') as f:
            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ฐานข้อมูลล่าสุด (.db)",
                data=f,
                file_name=db_filename,
                mime="application/x-sqlite3",
                help="กดปุ่มนี้หลังคีย์เสร็จ เพื่อเก็บข้อมูลล่าสุดไว้ในเครื่องคอมพิวเตอร์ของคุณ"
            )
    except:
        st.info("ยังไม่มีไฟล์ฐานข้อมูลให้ดาวน์โหลด เริ่มบันทึกข้อมูลก่อนนะคะ")
    
    st.write("---")
    
    # 2. ช่องสำหรับอัปโหลดไฟล์จากเครื่องกลับขึ้นออนไลน์ (กรณีข้อมูลหาย)
    uploaded_db = st.file_uploader("กู้คืนข้อมูล: เลือกไฟล์ .db ที่คุณเคยโหลดเก็บไว้มาวางตรงนี้", type="db")
    if uploaded_db is not None:
        with open(db_filename, "wb") as f:
            f.write(uploaded_db.getbuffer())
        st.success("✅ กู้คืนข้อมูลสำเร็จ! ระบบกำลังรีเฟรชหน้าจอ...")
        st.rerun()
