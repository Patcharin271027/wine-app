import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime, date

# 1. ตั้งค่าหน้าจอ
st.set_page_config(layout="wide", page_title="ระบบจัดการยอดขาย WINE Cloud")

# 2. เชื่อมต่อ Cloud Database
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except:
    st.error("⚠️ ไม่สามารถเชื่อมต่อฐานข้อมูลได้ กรุณาเช็กหน้า Secrets")
    st.stop()

st.title("🏨 ระบบจัดการยอดขาย Wine (Cloud Version)")

# --- แถบด้านซ้าย (Sidebar): ส่วนตั้งค่าโรงแรมและร้านค้า ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบ")
    
    # ส่วนจัดการโรงแรม
    with st.expander("🏢 เพิ่ม/ลบ รายชื่อโรงแรม"):
        new_h = st.text_input("ชื่อโรงแรมใหม่", key="sidebar_new_h")
        if st.button("บันทึกโรงแรม"):
            if new_h:
                try:
                    conn.table("hotels").insert({"name": new_h.strip()}).execute()
                    st.rerun()
                except: st.warning("มีชื่อนี้อยู่แล้ว")
        
        # ดึงข้อมูลโรงแรมมาแสดง
        h_res = conn.table("hotels").select("name").execute()
        h_data = pd.DataFrame(h_res.data) if h_res.data else pd.DataFrame(columns=['name'])
        st.dataframe(h_data, hide_index=True)
        
        h_list = h_data['name'].tolist() if not h_data.empty else []
        h_to_del = st.selectbox("เลือกโรงแรมที่จะลบ", [""] + h_list, key="sidebar_del_h")
        if st.button("ลบโรงแรม"):
            if h_to_del:
                conn.table("hotels").delete().eq("name", h_to_del).execute()
                st.rerun()

    # ส่วนจัดการร้านค้า
    with st.expander("🛍️ เพิ่ม/ลบ รายชื่อร้านค้า"):
        new_s = st.text_input("ชื่อร้านค้าใหม่", key="sidebar_new_s")
        if st.button("บันทึกร้านค้า"):
            if new_s:
                try:
                    conn.table("suppliers").insert({"name": new_s.strip()}).execute()
                    st.rerun()
                except: st.warning("มีชื่อนี้อยู่แล้ว")
        
        s_res = conn.table("suppliers").select("name").execute()
        s_data = pd.DataFrame(s_res.data) if s_res.data else pd.DataFrame(columns=['name'])
        st.dataframe(s_data, hide_index=True)
        
        s_list = s_data['name'].tolist() if not s_data.empty else []
        s_to_del = st.selectbox("เลือกร้านค้าที่จะลบ", [""] + s_list, key="sidebar_del_s")
        if st.button("ลบร้านค้า"):
            if s_to_del:
                conn.table("suppliers").delete().eq("name", s_to_del).execute()
                st.rerun()

# --- ส่วนบันทึกยอดขายและรายงาน (ใช้ตารางรายชื่อจาก Cloud) ---
st.subheader("📥 บันทึกยอดขาย WINE")
if not h_list or not s_list:
    st.info("💡 กรุณาเพิ่มรายชื่อ 'โรงแรม' และ 'ร้านค้า' ที่แถบด้านซ้ายมือก่อนนะคะ")
else:
    with st.form("main_sales_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        supplier_val = col1.selectbox("เลือก Supplier", s_list)
        stype_val = col1.radio("ประเภทการขาย", ["CONSIGNMENT", "CREDIT"], horizontal=True)
        hotel_val = col2.selectbox("เลือกโรงแรม", h_list)
        sale_date_val = col2.date_input("เลือกวันที่ขาย", date.today())
        amount_val = st.number_input("ยอดเงินยอดขาย (บาท)", min_value=0.0, step=1.0)
        
        if st.form_submit_button("บันทึกข้อมูล"):
            if amount_val > 0:
                conn.table("sales_data").insert({
                    "supplier": supplier_val, "stype": stype_val, 
                    "hotel": hotel_val, "sale_date": str(sale_date_val), "amount": amount_val
                }).execute()
                st.success(f"✅ บันทึกยอด {amount_val:,.2f} เรียบร้อย!")
                st.rerun()
