import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import date

st.set_page_config(layout="wide", page_title="ระบบยอดขาย WINE Cloud")
conn = st.connection("supabase", type=SupabaseConnection)

# --- ส่วนที่ 1: จัดการรายชื่อใน Sidebar ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบ")
    
    # จัดการ Supplier
    with st.expander("🏢 เพิ่ม/ลบ รายชื่อร้านค้า"):
        new_sup = st.text_input("ชื่อร้านค้าใหม่")
        if st.button("บันทึกร้านค้า"):
            if new_sup:
                conn.table("suppliers").insert({"name": new_sup}).execute()
                st.rerun()
        
        sups_data = conn.table("suppliers").select("name").execute().data
        for s in sups_data:
            col_s1, col_s2 = st.columns([3, 1])
            col_s1.text(s['name'])
            if col_s2.button("🗑️", key=f"del_s_{s['name']}"):
                conn.table("suppliers").delete().eq("name", s['name']).execute()
                st.rerun()

    # จัดการ โรงแรม
    with st.expander("🏨 เพิ่ม/ลบ รายชื่อโรงแรม"):
        new_hotel = st.text_input("ชื่อโรงแรมใหม่")
        if st.button("บันทึกโรงแรม"):
            if new_hotel:
                conn.table("hotels").insert({"name": new_hotel}).execute()
                st.rerun()
        
        hotels_data = conn.table("hotels").select("name").execute().data
        for h in hotels_data:
            col_h1, col_h2 = st.columns([3, 1])
            col_h1.text(h['name'])
            if col_h2.button("🗑️", key=f"del_h_{h['name']}"):
                conn.table("hotels").delete().eq("name", h['name']).execute()
                st.rerun()

# --- ส่วนที่ 2: ฟอร์มบันทึกยอดขาย ---
st.title("🏨 ระบบจัดการยอดขาย Wine (Cloud Version)")
st.subheader("📥 บันทึกยอดขาย WINE")

# ดึงรายชื่อจาก Database มาแสดงใน Selectbox
current_sups = [item['name'] for item in conn.table("suppliers").select("name").execute().data]
current_hotels = [item['name'] for item in conn.table("hotels").select("name").execute().data]

if not current_sups or not current_hotels:
    st.warning("⚠️ กรุณาเพิ่มชื่อร้านค้าและโรงแรมที่แถบด้านซ้ายก่อนเริ่มใช้งานค่ะ")
else:
    with st.form("main_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        sup_val = c1.selectbox("เลือก Supplier", current_sups)
        stype_val = c1.radio("ประเภทการขาย", ["CONSIGNMENT", "CREDIT"], horizontal=True)
        hotel_val = c2.selectbox("เลือกโรงแรม", current_hotels)
        date_val = c2.date_input("วันที่ขาย", date.today())
        amt_val = st.number_input("ยอดเงิน (บาท)", min_value=0.0)
        
        if st.form_submit_button("บันทึกข้อมูล"):
            if amt_val > 0:
                conn.table("sales_data").insert({
                    "supplier": sup_val, "stype": stype_val, 
                    "hotel": hotel_val, "sale_date": str(date_val), "amount": amt_val
                }).execute()
                st.success("✅ บันทึกยอดลง Cloud เรียบร้อย!")
                st.rerun()

# --- ส่วนที่ 3: รายงาน ---
st.divider()
try:
    res = conn.table("sales_data").select("*").execute()
    if res.data:
        st.subheader("📊 รายงานสรุปยอดขาย")
        st.dataframe(pd.DataFrame(res.data), use_container_width=True)
except:
    st.info("กำลังรอข้อมูลรายการแรก...")
