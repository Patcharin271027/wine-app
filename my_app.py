import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import date

# 1. ตั้งค่าหน้าจอ
st.set_page_config(layout="wide", page_title="ระบบยอดขาย WINE Cloud")

# 2. เชื่อมต่อ Cloud Database
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้: {e}")
    st.info("กรุณาตรวจสอบหน้า Secrets ว่าตั้งค่า [connections.supabase] ถูกต้องหรือไม่")
    st.stop()

# --- ส่วนที่ 1: จัดการรายชื่อใน Sidebar ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบ")
    
    # จัดการ Supplier
    with st.expander("🏢 เพิ่ม/ลบ รายชื่อร้านค้า"):
        new_sup = st.text_input("ชื่อร้านค้าใหม่")
        if st.button("บันทึกร้านค้า"):
            if new_sup:
                try:
                    conn.table("suppliers").insert({"name": new_sup}).execute()
                    st.success("บันทึกสำเร็จ")
                    st.rerun()
                except:
                    st.error("เกิดข้อผิดพลาดในการบันทึก")
        
        try:
            res_s = conn.table("suppliers").select("name").execute()
            sups_list = res_s.data if res_s.data else []
            for s in sups_list:
                c1, c2 = st.columns([3, 1])
                c1.text(s['name'])
                if c2.button("🗑️", key=f"del_s_{s['name']}"):
                    conn.table("suppliers").delete().eq("name", s['name']).execute()
                    st.rerun()
        except:
            st.caption("ยังไม่มีข้อมูลร้านค้า")

    # จัดการ โรงแรม
    with st.expander("🏨 เพิ่ม/ลบ รายชื่อโรงแรม"):
        new_hotel = st.text_input("ชื่อโรงแรมใหม่")
        if st.button("บันทึกโรงแรม"):
            if new_hotel:
                try:
                    conn.table("hotels").insert({"name": new_hotel}).execute()
                    st.success("บันทึกสำเร็จ")
                    st.rerun()
                except:
                    st.error("เกิดข้อผิดพลาด")
        
        try:
            res_h = conn.table("hotels").select("name").execute()
            hotels_list = res_h.data if res_h.data else []
            for h in hotels_list:
                c1, c2 = st.columns([3, 1])
                c1.text(h['name'])
                if c2.button("🗑️", key=f"del_h_{h['name']}"):
                    conn.table("hotels").delete().eq("name", h['name']).execute()
                    st.rerun()
        except:
            st.caption("ยังไม่มีข้อมูลโรงแรม")

# --- ส่วนที่ 2: ฟอร์มบันทึกยอดขาย ---
st.title("🏨 ระบบจัดการยอดขาย Wine (Cloud Version)")
st.subheader("📥 บันทึกยอดขาย WINE")

# ดึงรายชื่อมาแสดงในฟอร์ม
try:
    current_sups = [item['name'] for item in conn.table("suppliers").select("name").execute().data]
    current_hotels = [item['name'] for item in conn.table("hotels").select("name").execute().data]
except:
    current_sups, current_hotels = [], []

if not current_sups or not current_hotels:
    st.warning("⚠️ กรุณาเพิ่มชื่อร้านค้าและโรงแรมที่แถบด้านซ้ายก่อนเริ่มใช้งานค่ะ")
else:
    with st.form("main_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        sup_val = col1.selectbox("เลือก Supplier", current_sups)
        stype_val = col1.radio("ประเภทการขาย", ["CONSIGNMENT", "CREDIT"], horizontal=True)
        hotel_val = col2.selectbox("เลือกโรงแรม", current_hotels)
        date_val = col2.date_input("วันที่ขาย", date.today())
        amt_val = st.number_input("ยอดเงิน (บาท)", min_value=0.0)
        
        if st.form_submit_button("บันทึกข้อมูล"):
            if amt_val > 0:
                try:
                    conn.table("sales_data").insert({
                        "supplier": sup_val, "stype": stype_val, 
                        "hotel": hotel_val, "sale_date": str(date_val), "amount": amt_val
                    }).execute()
                    st.success("✅ บันทึกยอดลง Cloud เรียบร้อย!")
                    st.rerun()
                except Exception as e:
                    st.error(f"บันทึกไม่สำเร็จ: {e}")

# --- ส่วนที่ 3: รายงาน ---
st.divider()
st.subheader("📊 รายงานสรุปยอดขาย")
try:
    report_res = conn.table("sales_data").select("*").execute()
    if report_res.data:
        st.dataframe(pd.DataFrame(report_res.data), use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลการขายในระบบ")
except:
    st.info("กำลังรอข้อมูลรายการแรก...")
