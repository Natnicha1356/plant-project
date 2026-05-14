import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import pandas as pd
from datetime import datetime
import os

# --- 1. การตั้งค่าหน้าเว็บ (Branding & Layout) ---
st.set_page_config(page_title="South Bangkok Digital Port", layout="wide", initial_sidebar_state="expanded")

# ปรับแต่ง CSS ให้หน้าเว็บดูทันสมัยแบบ Industrial Dashboard
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #ffffff; border-radius: 5px 5px 0 0; gap: 8px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #004a99; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ส่วนหัวเว็บไซต์ ---
st.title("🏭 South Bangkok Power Plant - Digital Monitoring Port")
st.markdown(f"**สถานะระบบ:** 🟢 ออนไลน์ | **วันที่:** {datetime.now().strftime('%d %B %Y')} | **ผู้บันทึก:** Trainee Team")
st.divider()

# --- 3. ฟังก์ชันประมวลผล (Backend Logic) ---
@st.cache_resource
def load_model():
    return easyocr.Reader(['en'], gpu=False)
def log_data(unit_name, extracted_texts):
    """ฟังก์ชันบันทึกข้อมูลแยกตามชื่อเครื่องลงฐานข้อมูล CSV"""
    filename = f"database_{unit_name}.csv"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # กรองเอาเฉพาะข้อความที่มีตัวเลข (ซึ่งมักจะเป็นค่า Parameter)
    values = [txt for txt in extracted_texts if any(char.isdigit() for char in txt)]
    
    new_row = {
        "Timestamp": timestamp,
        "Machine_Unit": unit_name,
        "Extracted_Data": " | ".join(values)
    }
    
    df_new = pd.DataFrame([new_row])
    if not os.path.isfile(filename):
        df_new.to_csv(filename, index=False, encoding='utf-8-sig')
    else:
        df_new.to_csv(filename, mode='a', header=False, index=False, encoding='utf-8-sig')
    return filename

# --- 4. การสร้างเมนูหน้าจอ (Navigation Tabs) ---
# สร้าง Tab ตามหน้าจอ HMI ที่คุณต้องการ
tab_names = ["🔥 GT 10", "💨 ST 10", "🚰 HRSG 10", "💧 CONDENSATE", "🗄️ CENTRAL DATABASE"]
tabs = st.tabs(tab_names)

units = ["GT10_Gas_Turbine", "ST10_Steam_Turbine", "HRSG10_Boiler", "Main_Condensate"]

# ลูปสร้างหน้าทำงานให้แต่ละเครื่อง (4 หน้าแรก)
for i in range(4):
    with tabs[i]:
        unit_id = units[i]
        st.header(f"บันทึกข้อมูลหน้าจอ: {unit_id.replace('_', ' ')}")
        
        col_up, col_res = st.columns([1, 1])
        
        with col_up:
            st.subheader("📤 อัปโหลดรูปภาพ HMI")
            file = st.file_uploader(f"เลือกภาพถ่ายหน้าจอ {unit_id}", type=["jpg", "png", "jpeg"], key=f"file_{unit_id}")
            if file:
                img = Image.open(file)
                st.image(img, use_container_width=True)
                
                if st.button(f"เริ่มสแกนและบันทึก {unit_id}", key=f"btn_{unit_id}"):
                    with st.spinner('AI กำลังสกัดข้อมูล...'):
                        reader = load_model()
                        results = reader.readtext(np.array(img))
                        texts = [res[1] for res in results]
                        
                        db_file = log_data(unit_id, texts)
                        st.success(f"บันทึกข้อมูล {unit_id} สำเร็จ!")
                        st.toast("Data Saved to Local Database")

        with col_res:
            st.subheader("📋 ประวัติการบันทึกล่าสุด")
            db_path = f"database_{unit_id}.csv"
            if os.path.exists(db_path):
                history = pd.read_csv(db_path)
                st.dataframe(history.tail(5), use_container_width=True)
            else:
                st.info("ยังไม่มีข้อมูลบันทึกสำหรับเครื่องนี้")

# --- 5. หน้าฐานข้อมูลกลาง (Central Database Tab) ---
with tabs[4]:
    st.header("🗄️ ศูนย์รวมข้อมูลโรงไฟฟ้า (Central Repository)")
    target_unit = st.selectbox("เลือกฐานข้อมูลเครื่องที่ต้องการตรวจสอบ:", units)
    
    db_name = f"database_{target_unit}.csv"
    if os.path.exists(db_name):
        full_df = pd.read_csv(db_name)
        st.subheader(f"ตารางข้อมูลทั้งหมดของ {target_unit}")
        st.dataframe(full_df, use_container_width=True)
        
        # ส่วนงานส่งออกข้อมูลสำหรับวิศวกร (Export for Report)
        csv_data = full_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label=f"📥 ดาวน์โหลดไฟล์ Excel ({target_unit})",
            data=csv_data,
            file_name=f"Report_{target_unit}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("ไม่พบไฟล์ฐานข้อมูล กรุณาทำการบันทึกข้อมูลในหน้าเครื่องจักรที่ต้องการก่อน")
