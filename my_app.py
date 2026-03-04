import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import date

# 1. ตั้งค่าหน้าจอ
st.set_page_config(layout="wide", page_title="ระบบจัดการยอดขาย WINE")

# 2. เชื่อมต่อ Cloud Database (Supabase)
conn = st.connection("supabase", type=SupabaseConnection)

st.title("🏨 ระบบจัดการยอดขาย Wine (Cloud Version)")

# --- ส่วนที่ 1: ฟอร์มบันทึกยอดขาย ---
st.subheader("📥 บันทึกยอดขาย WINE")

# กำหนดรายชื่อเพื่อให้ใช้งานร่วมกันได้ทันที
suppliers_options = ["AMBROSE", "IWS", "ITALTHAI", "WINE DEE DEE"]
hotels_options = ["2 SAN", "HOTEL A", "HOTEL B"]

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
            # บันทึกข้อมูลลง Cloud ทันที
            new_data = {
                "supplier": supplier_val,
                "stype": stype_val,
                "hotel": hotel_val,
                "sale_date": str(sale_date_val),
                "amount": amount_val
            }
            try:
                conn.table("sales_data").insert(new_data).execute()
                st.success(f"✅ บันทึกยอด {amount_val:,.2f} ลง Cloud สำเร็จ!")
                st.rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการบันทึก: {e}")
        else:
            st.error("❌ กรุณาใส่ยอดเงินที่มากกว่า 0")

# --- ส่วนที่ 2: รายงานดึงจาก Cloud ---
st.divider()
st.subheader("📊 รายงานสรุปยอดขาย (Real-time Cloud)")

try:
    # ดึงข้อมูลทั้งหมดจาก Supabase
    res = conn.table("sales_data").select("*").execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        df['sale_date'] = pd.to_datetime(df['sale_date'])
        
        # ตัวกรองรายงาน
        f_col1, f_col2 = st.columns(2)
        start_f = f_col1.date_input("จากวันที่", date.today().replace(day=1))
        end_f = f_col2.date_input("ถึงวันที่", date.today())

        mask = (df['sale_date'].dt.date >= start_f) & (df['sale_date'].dt.date <= end_f)
        df_filtered = df.loc[mask].copy()

        if not df_filtered.empty:
            # ทำตารางสรุป
            pivot = df_filtered.pivot_table(index=['supplier', 'hotel'], 
                                           columns=df_filtered['sale_date'].dt.strftime('%b-%y'), 
                                           values='amount', aggfunc='sum', fill_value=0)
            st.dataframe(pivot, use_container_width=True)
        else:
            st.warning("ไม่มีข้อมูลในช่วงวันที่เลือก")
    else:
        st.info("ยังไม่มีข้อมูลในระบบ Cloud เริ่มบันทึกได้เลยค่ะ")
except Exception as e:
    st.info("กำลังรอการเชื่อมต่อฐานข้อมูลครั้งแรก...")
