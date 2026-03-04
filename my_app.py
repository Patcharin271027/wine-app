import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from datetime import datetime, date
import io

# 1. ตั้งค่าหน้าจอ
st.set_page_config(layout="wide", page_title="ระบบจัดการยอดขาย WINE Cloud")

# 2. เชื่อมต่อ Cloud Database
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้: {e}")
    st.stop()

st.title("🏨 ระบบจัดการยอดขาย Wine (Cloud Version)")

# --- แถบด้านซ้าย (Sidebar): ส่วนตั้งค่าโรงแรมและร้านค้า ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าระบบ")
    
    # ดึงข้อมูลโรงแรมและร้านค้ามาแสดง
    try:
        h_res = conn.table("hotels").select("name").execute()
        h_list = sorted([i['name'] for i in h_res.data]) if h_res.data else []
        
        s_res = conn.table("suppliers").select("name").execute()
        s_list = sorted([i['name'] for i in s_res.data]) if s_res.data else []
    except:
        h_list, s_list = [], []

    with st.expander("🏢 เพิ่ม/ลบ รายชื่อโรงแรม"):
        new_h = st.text_input("ชื่อโรงแรมใหม่", key="sidebar_new_h")
        if st.button("บันทึกโรงแรม"):
            if new_h:
                conn.table("hotels").insert({"name": new_h.strip()}).execute()
                st.rerun()
        
        h_to_del = st.selectbox("เลือกโรงแรมที่จะลบ", [""] + h_list, key="sidebar_del_h")
        if st.button("ลบโรงแรม"):
            if h_to_del:
                conn.table("hotels").delete().eq("name", h_to_del).execute()
                st.rerun()

    with st.expander("🛍️ เพิ่ม/ลบ รายชื่อร้านค้า"):
        new_s = st.text_input("ชื่อร้านค้าใหม่", key="sidebar_new_s")
        if st.button("บันทึกร้านค้า"):
            if new_s:
                conn.table("suppliers").insert({"name": new_s.strip()}).execute()
                st.rerun()
        
        s_to_del = st.selectbox("เลือกร้านค้าที่จะลบ", [""] + s_list, key="sidebar_del_s")
        if st.button("ลบร้านค้า"):
            if s_to_del:
                conn.table("suppliers").delete().eq("name", s_to_del).execute()
                st.rerun()

# --- ส่วนที่ 1: ฟอร์มบันทึกยอดขาย ---
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
                st.success(f"✅ บันทึกยอด {amount_val:,.2f} บาท เรียบร้อย!")
                st.rerun()

# --- ส่วนที่ 2: รายงานและการกรองข้อมูล ---
st.divider()
st.subheader("📊 รายงานสรุปยอดขาย WINE")

try:
    report_res = conn.table("sales_data").select("*").execute()
    df_raw = pd.DataFrame(report_res.data) if report_res.data else pd.DataFrame()

    if not df_raw.empty:
        df_raw['sale_date'] = pd.to_datetime(df_raw['sale_date'])
        
        with st.container(border=True):
            st.write("🔍 **ตัวกรองรายงาน**")
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            f_sup = f_col1.multiselect("Supplier", s_list, default=s_list)
            f_type = f_col2.multiselect("Type", ["CONSIGNMENT", "CREDIT"], default=["CONSIGNMENT", "CREDIT"])
            start_filter = f_col3.date_input("วันที่เริ่มต้น", date.today().replace(day=1))
            end_filter = f_col4.date_input("วันที่สิ้นสุด", date.today())

        mask = (df_raw['supplier'].isin(f_sup)) & \
               (df_raw['stype'].isin(f_type)) & \
               (df_raw['sale_date'].dt.date >= start_filter) & \
               (df_raw['sale_date'].dt.date <= end_filter)
        
        df_filtered = df_raw.loc[mask].copy()

        if not df_filtered.empty:
            # --- แก้ไขการเรียงลำดับเดือน (เก่าไปใหม่) ---
            df_filtered = df_filtered.sort_values('sale_date')
            df_filtered['month_year'] = df_filtered['sale_date'].dt.strftime('%b-%y')
            
            pivot = df_filtered.pivot_table(index=['supplier', 'stype', 'hotel'], 
                                            columns='month_year', values='amount', 
                                            aggfunc='sum', fill_value=0, margins=True, 
                                            margins_name='TOTAL', sort=False)
            
            st.write("📈 **ตารางสรุปยอดขาย (เรียงตามลำดับเดือน)**")
            styled_pivot = pivot.style.format("{:,.0f}")
            st.dataframe(pivot, use_container_width=True)
            
            # ปุ่มดาวน์โหลด Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                pivot.to_excel(writer, sheet_name='Monthly_Report')
            st.download_button("💾 ดาวน์โหลดรายงาน Excel", data=buffer, file_name=f"wine_report_{date.today()}.xlsx")
            
            # --- ส่วนที่ 3: ระบบแก้ไข/ลบข้อมูล ---
            st.write("---")
            st.write("✏️ **จัดการข้อมูลที่บันทึกผิด**")
            with st.expander("แสดงรายการข้อมูลดิบเพื่อ แก้ไข หรือ ลบ"):
                manage_df = df_filtered[['id', 'supplier', 'stype', 'hotel', 'sale_date', 'amount']].copy()
                manage_df['sale_date'] = manage_df['sale_date'].dt.date
                st.dataframe(manage_df, hide_index=True)
                
                m_col1, m_col2, m_col3 = st.columns([1,2,1])
                target_id = m_col1.number_input("ระบุ ID ที่ต้องการจัดการ", min_value=1, step=1)
                edit_amount = m_col2.number_input("ยอดเงินใหม่", min_value=0.0)
                
                if m_col3.button("🔄 อัปเดตยอดเงิน", use_container_width=True):
                    conn.table("sales_data").update({"amount": edit_amount}).eq("id", target_id).execute()
                    st.success("อัปเดตสำเร็จ!")
                    st.rerun()
                    
                if m_col3.button("🗑️ ลบข้อมูล", type="primary", use_container_width=True):
                    conn.table("sales_data").delete().eq("id", target_id).execute()
                    st.warning("ลบข้อมูลเรียบร้อย!")
                    st.rerun()
        else:
            st.warning("⚠️ ไม่พบข้อมูลในช่วงเวลาที่เลือก")
    else:
        st.info("ยังไม่มีข้อมูลในระบบ เริ่มบันทึกข้อมูลด้านบนได้เลยค่ะ")
except Exception as e:
    st.info("กำลังรอการเชื่อมต่อข้อมูล...")

