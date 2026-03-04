import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import date

# 1. ตั้งค่าหน้าจอ
st.set_page_config(layout="wide", page_title="ระบบจัดการยอดขาย WINE")

# 2. เชื่อมต่อ Cloud Database
conn = st.connection("supabase", type=SupabaseConnection)

st.title("🏨 ระบบจัดการยอดขาย Wine (Cloud Version)")

# --- ส่วนที่ 1: บันทึกข้อมูล ---
st.subheader("📥 บันทึกยอดขาย WINE")

# รายชื่อโรงแรมและร้านค้า (คุณสามารถมาแก้เพิ่มตรงนี้ได้ตลอดค่ะ)
suppliers_options = ["AMBROSE", "IWS", "ITALTHAI", "WINE DEE DEE", "BKK BEVERAGE"]
hotels_options = ["2 SAN", "HOTEL A", "HOTEL B", "CASA DE LA FLORA", "LA VELA"]

with st.form("sales_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    sup = col1.selectbox("Supplier", suppliers_options)
    stype = col1.radio("ประเภท", ["CONSIGNMENT", "CREDIT"], horizontal=True)
    hot = col2.selectbox("โรงแรม", hotels_options)
    s_date = col2.date_input("วันที่", date.today())
    amt = st.number_input("ยอดเงิน (บาท)", min_value=0.0)
    
    if st.form_submit_button("บันทึกข้อมูล"):
        if amt > 0:
            row = {"supplier": sup, "stype": stype, "hotel": hot, "sale_date": str(s_date), "amount": amt}
            try:
                conn.table("sales_data").insert(row).execute()
                st.success(f"✅ บันทึกยอด {amt:,.2f} ลง Cloud เรียบร้อย!")
                st.rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")

# --- ส่วนที่ 2: แสดงรายงาน ---
st.divider()
try:
    res = conn.table("sales_data").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        st.subheader("📊 รายงานยอดขายสะสมบน Cloud")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลบน Cloud เริ่มบันทึกได้เลยค่ะ")
except:
    st.warning("กำลังรอการเชื่อมต่อกับ Supabase...")
