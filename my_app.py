import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime, date

# 1. ตั้งค่าหน้าจอ (เหมือนเดิมของคุณ)
st.set_page_config(layout="wide", page_title="ระบบจัดการยอดขาย WINE Cloud")

# 2. เชื่อมต่อ Cloud Database (เปลี่ยนจาก SQLite)
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except:
    st.error("⚠️ เชื่อมต่อ Cloud ไม่ได้ กรุณาเช็กหน้า Secrets ค่ะ")
    st.stop()

st.title("🏨 ระบบจัดการยอดขาย Wine (Cloud Version)")

# --- แถบด้านซ้าย (Sidebar): ดึงข้อมูลจาก Cloud ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบ")
    
    # ดึงข้อมูลโรงแรมจาก Cloud
    h_res = conn.table("hotels").select("name").execute()
    h_data = pd.DataFrame(h_res.data) if h_res.data else pd.DataFrame(columns=['name'])

    with st.expander("🏢 เพิ่ม/ลบ รายชื่อโรงแรม"):
        new_h = st.text_input("ชื่อโรงแรมใหม่", key="sidebar_new_h")
        if st.button("บันทึกโรงแรม"):
            if new_h:
                try:
                    conn.table("hotels").insert({"name": new_h.strip()}).execute()
                    st.rerun()
                except: st.warning("มีชื่อนี้อยู่แล้ว")
        
        st.dataframe(h_data, hide_index=True)
        h_to_del = st.selectbox("เลือกโรงแรมที่จะลบ", [""] + h_data['name'].tolist(), key="sidebar_del_h")
        if st.button("ลบโรงแรม"):
            conn.table("hotels").delete().eq("name", h_to_del).execute()
            st.rerun()

    # ดึงข้อมูลร้านค้าจาก Cloud
    s_res = conn.table("suppliers").select("name").execute()
    s_data = pd.DataFrame(s_res.data) if s_res.data else pd.DataFrame(columns=['name'])

    with st.expander("🛍️ เพิ่ม/ลบ รายชื่อร้านค้า"):
        new_s = st.text_input("ชื่อร้านค้าใหม่", key="sidebar_new_s")
        if st.button("บันทึกร้านค้า"):
            if new_s:
                try:
                    conn.table("suppliers").insert({"name": new_s.strip()}).execute()
                    st.rerun()
                except: st.warning("มีชื่อนี้อยู่แล้ว")
        
        st.dataframe(s_data, hide_index=True)
        s_to_del = st.selectbox("เลือกร้านค้าที่จะลบ", [""] + s_data['name'].tolist(), key="sidebar_del_s")
        if st.button("ลบร้านค้า"):
            conn.table("suppliers").delete().eq("name", s_to_del).execute()
            st.rerun()

# --- ส่วนที่ 1: ฟอร์มบันทึกยอดขาย (คงฟังก์ชันเดิมของคุณไว้) ---
st.subheader("📥 บันทึกยอดขาย WINE")
hotels_options = h_data['name'].tolist()
suppliers_options = s_data['name'].tolist()

if not hotels_options or not suppliers_options:
    st.info("💡 กรุณาเพิ่มรายชื่อ 'โรงแรม' และ 'ร้านค้า' ที่แถบด้านซ้ายมือก่อนนะคะ")
else:
    with st.form("main_sales_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        supplier_val = col1.selectbox("เลือก Supplier", suppliers_options)
        stype_val = col1.radio("ประเภทการขาย", ["CONSIGNMENT", "CREDIT"], horizontal=True)
        hotel_val = col2.selectbox("เลือกโรงแรม", hotels_options)
        sale_date_val = col2.date_input("เลือกวันที่ขาย", date.today())
        amount_val = st.number_input("ยอดเงินยอดขาย (บาท)", min_value=0.0, step=1.0)
        
        if st.form_submit_button("บันทึกข้อมูล"):
            if amount_val > 0:
                conn.table("sales_data").insert({
                    "supplier": supplier_val, "stype": stype_val, 
                    "hotel": hotel_val, "sale_date": str(sale_date_val), "amount": amount_val
                }).execute()
                st.success(f"✅ บันทึกยอด {amount_val:,.2f} บาท เรียบร้อยแล้ว!")
                st.rerun()
            else:
                st.error("❌ กรุณาใส่ยอดเงินที่มากกว่า 0")

# --- ส่วนที่ 2: รายงาน (ดึงจาก Cloud) ---
st.divider()
st.subheader("📊 รายงานสรุปยอดขาย WINE")

sales_res = conn.table("sales_data").select("*").execute()
df_raw = pd.DataFrame(sales_res.data) if sales_res.data else pd.DataFrame()

if not df_raw.empty:
    df_raw['sale_date'] = pd.to_datetime(df_raw['sale_date'])
    # ... (ส่วนการกรองข้อมูลและ Pivot Table ใช้โค้ดเดิมของคุณได้เลยค่ะ) ...
    st.write("🔍 ตัวกรองรายงาน")
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    f_sup = f_col1.multiselect("Supplier", suppliers_options, default=suppliers_options)
    f_type = f_col2.multiselect("Type", ["CONSIGNMENT", "CREDIT"], default=["CONSIGNMENT", "CREDIT"])
    start_filter = f_col3.date_input("วันที่เริ่มต้น", date.today().replace(day=1))
    end_filter = f_col4.date_input("วันที่สิ้นสุด", date.today())

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
        
        # ระบบจัดการข้อมูล (แก้ไข/ลบ)
        st.write("---")
        st.write("✏️ **จัดการข้อมูลที่บันทึกผิด**")
        target_id = st.number_input("ระบุ ID ที่ต้องการลบ/แก้ไข", min_value=1, step=1)
        if st.button("🗑️ ลบข้อมูลรายการนี้"):
            conn.table("sales_data").delete().eq("id", target_id).execute()
            st.rerun()
