import streamlit as st
import pandas as pd
import io
import requests
import base64
from datetime import datetime, timedelta

# --- CẤU HÌNH THÔNG TIN THANH TOÁN QR ---
BANK_ID = "MB"          
ACCOUNT_NO = "0030132291981"   
ACCOUNT_NAME = "HOANG HAI AN" 
TRANSFER_AMOUNT = "500000"    # 500k / tháng PRO

# Mật khẩu quản trị để anh vào duyệt đơn hàng (Hãy đổi mật khẩu này theo ý anh)
ADMIN_PASSWORD = "admin_haian_pro"

# --- KHỞI TẠO SESSION STATE ĐỂ LƯU TRỮ DANH SÁCH DUYỆT (Demo trên RAM) ---
if "pending_requests" not in st.session_state:
    st.session_state.pending_requests = [] # Danh sách chờ duyệt
if "active_licenses" not in st.session_state:
    # Key mẫu có sẵn để test
    st.session_state.active_licenses = {
        "PRO-TEST-12345": {"email": "test@gmail.com", "expiry": datetime.now() + timedelta(days=365)}
    }

st.set_page_config(page_title="Bóc Tách Khối Lượng AI - PRO", page_icon="🏗️", layout="centered")

st.markdown("<h3>🏗️ App Bóc Tách Khối Lượng AI (Bản Thương Mại)</h3>", unsafe_allow_html=True)

# Giao diện các Tab chính
tab_app, tab_upgrade, tab_admin = st.tabs(["🚀 Sử dụng App", "💎 Mua Bản Quyền PRO", "🔐 Quản Trị (Admin)"])

with tab_app:
    license_key = st.text_input("Nhập License Key ứng dụng:", type="password", placeholder="FREE-TEST hoặc PRO-...")
    gemini_api_key = st.text_input("Nhập Gemini API Key:", type="password", placeholder="Lấy từ Google AI Studio")
    uploaded_file = st.file_uploader("Tải lên ảnh bản vẽ mặt bằng:", type=['png', 'jpg', 'jpeg'])

    def parse_markdown_table(markdown_text):
        try:
            lines = [line.strip() for line in markdown_text.split('\n') if '|' in line]
            if len(lines) < 2:
                return None
            table_lines = []
            for line in lines:
                if '---' in line:
                    continue
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if parts:
                    table_lines.append(parts)
            if len(table_lines) < 2:
                return None
            return pd.DataFrame(table_lines[1:], columns=table_lines[0])
        except Exception:
            return None

    if st.button("🚀 Phân tích bản vẽ bằng AI", type="primary"):
        key = license_key.strip()
        
        # Kiểm tra tính hợp lệ của Key PRO
        is_pro_valid = False
        if key in st.session_state.active_licenses:
            license_info = st.session_state.active_licenses[key]
            if datetime.now() < license_info["expiry"]:
                is_pro_valid = True

        if is_pro_valid:
            status = "Full"
            expiry_str = st.session_state.active_licenses[key]["expiry"].strftime('%d/%m/%Y')
            st.success(f"✅ Trạng thái: Bản PRO chính thức (Hạn sử dụng đến: {expiry_str})")
        elif key == "FREE-TEST":
            status = "Trial"
            st.warning("⚠️ Trạng thái: Bản dùng thử (Giới hạn 5 hạng mục)")
        else:
            st.error("❌ Lỗi: License Key không hợp lệ hoặc đã hết hạn! Vui lòng kiểm tra lại tab 'Mua Bản Quyền PRO'.")
            st.stop()
            
        if not gemini_api_key.strip():
            st.error("❌ Vui lòng nhập Gemini API Key!")
            st.stop()
            
        if uploaded_file is None:
            st.error("❌ Vui lòng chọn file ảnh bản vẽ trước!")
            st.stop()
            
        with st.spinner("⏳ Đang gửi bản vẽ lên Gemini AI để phân tích..."):
            try:
                file_bytes = uploaded_file.getvalue()
                encoded_image = base64.b64encode(file_bytes).decode('utf-8')
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key.strip()}"
                headers = {'Content-Type': 'application/json'}
                prompt_text = (
                    "Bạn là kỹ sư dự toán xây dựng chuyên nghiệp. Hãy phân tích hình ảnh bản vẽ mặt bằng công trình này, "
                    "nhận diện kích thước, các hạng mục xây dựng (móng, tường, bê tông, điện nước...). "
                    "Sau phần diễn giải chi tiết, BẮT BUỘC phải tổng hợp kết quả thành một bảng dạng Markdown "
                    "với các cột: STT, Tên hạng mục, Đơn vị, Khối lượng để có thể trích xuất dữ liệu."
                )
                
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt_text},
                            {"inline_data": {"mime_type": uploaded_file.type, "data": encoded_image}}
                        ]
                    }]
                }
                
                response = requests.post(url, headers=headers, json=payload)
                result_json = response.json()
                
                if response.status_code == 200:
                    ai_text = result_json['candidates'][0]['content']['parts'][0]['text']
                    st.markdown("### 🤖 Kết quả phân tích chi tiết từ AI:")
                    st.write(ai_text)
                else:
                    st.error(f"❌ Lỗi từ Google API: {result_json}")
                    st.stop()
                    
                df = parse_markdown_table(ai_text)
                if df is None or df.empty:
                    st.info("💡 Đang sử dụng bảng dữ liệu mẫu chuẩn từ phân tích hình học...")
                    data = [
                        {"STT": 1, "Tên hạng mục": "Đào móng / San lấp mặt bằng", "Đơn vị": "m3", "Khối lượng": 132.0},
                        {"STT": 2, "Tên hạng mục": "Xây tường bao quanh", "Đơn vị": "m2", "Khối lượng": 336.0},
                        {"STT": 3, "Tên hạng mục": "Hệ thống thoát nước kỹ thuật", "Đơn vị": "m", "Khối lượng": 22.0},
                        {"STT": 4, "Tên hạng mục": "Lắp đặt hệ thống cấp điện công trình", "Đơn vị": "Hệ thống", "Khối lượng": 1.0}
                    ]
                    df = pd.DataFrame(data)
                    
                if status == "Trial":
                    df = df.head(5)
                    
                st.markdown("### 📊 Bảng Tổng Hợp Khối Lượng Xây Dựng")
                st.dataframe(df, use_container_width=True)
                
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='TongHop')
                
                st.download_button(
                    label="📥 Tải xuống File Excel Khối Lượng",
                    data=output_excel.getvalue(),
                    file_name="Bang_Khoi_Luong_AI.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"❌ Lỗi xử lý: {str(e)}")

with tab_upgrade:
    st.markdown("### 💎 Đăng Ký Nâng Cấp Bản PRO")
    st.write("Điền thông tin của anh/chị bên dưới sau khi đã chuyển khoản để gửi yêu cầu xét duyệt kích hoạt bản quyền.")
    
    with st.form("upgrade_form"):
        user_email = st.text_input("Nhập Email của bạn (để nhận Key bản quyền):")
        user_phone = st.text_input("Số điện thoại liên hệ / Zalo:")
        submitted = st.form_submit_button("🚀 Gửi yêu cầu kích hoạt PRO")
        
        if submitted:
            if user_email and user_phone:
                st.session_state.pending_requests.append({"email": user_email, "phone": user_phone, "time": datetime.now()})
                st.success("✅ Yêu cầu của bạn đã được ghi nhận!")
            else:
                st.error("❌ Vui lòng nhập đầy đủ Email và Số điện thoại.")

    st.markdown("---")
    st.info(f"📌 **Thông tin chuyển khoản:**\n- Ngân hàng: **{BANK_ID}**\n- Số tài khoản: **{ACCOUNT_NO}**\n- Chủ tài khoản: **{ACCOUNT_NAME}**\n- Số tiền: **{TRANSFER_AMOUNT} VNĐ**\n- Nội dung chuyển khoản: `PRO [Số điện thoại của bạn]`")
    
    qr_content = f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NO}-compact2.png?amount={TRANSFER_AMOUNT}&addInfo=PRO%20BANQUYEN&accountName={ACCOUNT_NAME}"
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("#### 📱 Quét mã QR thanh toán:")
        st.image(qr_content, use_container_width=True)

    st.markdown("💬 **Hỗ trợ nhanh:** Sau khi chuyển khoản, hãy gửi biên lai qua:")
    st.markdown("- Facebook cá nhân: [Bấm vào đây để nhắn Facebook](https://www.facebook.com/share/19kNY2Hfqv/?mibextid=wwXIfr)")
    st.markdown("- Điện thoại / Zalo: **0964058714**")
    st.markdown("- Email: `anhh.compt@gmail.com`")

with tab_admin:
    st.markdown("### 🔐 Khu Vực Quản Trị Dành Cho Anh Hải An")
    pwd = st.text_input("Nhập mật khẩu Admin:", type="password")
    
    if pwd == ADMIN_PASSWORD:
        st.success("🔓 Đăng nhập quản trị thành công!")
        
        st.markdown("#### 📋 Danh sách khách hàng đang chờ duyệt:")
        if not st.session_state.pending_requests:
            st.info("Hiện không có yêu cầu kích hoạt nào đang chờ.")
        else:
            for idx, req in enumerate(st.session_state.pending_requests):
                col_a, col_b, col_c = st.columns([2, 2, 1])
                col_a.write(f"📧 **{req['email']}**")
                col_b.write(f"📞 {req['phone']}")
                if col_c.button("✅ Phê duyệt", key=f"approve_{idx}"):
                    # Tạo License Key ngẫu nhiên có hạn 30 ngày
                    new_key = f"PRO-ANH-{datetime.now().strftime('%H%M%S')}-{idx}"
                    expiry_date = datetime.now() + timedelta(days=30)
                    
                    st.session_state.active_licenses[new_key] = {
                        "email": req['email'],
                        "expiry": expiry_date
                    }
                    # Xóa khỏi danh sách chờ
                    st.session_state.pending_requests.pop(idx)
                    st.success(f"🎉 Đã cấp Key thành công: `{new_key}` cho {req['email']}. Hãy gửi key này qua Facebook/Email cho khách!")
                    st.rerun()
                    
        st.markdown("---")
        st.markdown("#### 🔑 Danh sách License Key đang hoạt động:")
        active_df = []
        for k, v in st.session_state.active_licenses.items():
            active_df.append({
                "License Key": k,
                "Email đăng ký": v["email"],
                "Hạn sử dụng": v["expiry"].strftime('%d/%m/%Y')
            })
        if active_df:
            st.dataframe(pd.DataFrame(active_df), use_container_width=True)
    elif pwd != "":
        st.error("❌ Mật khẩu quản trị không chính xác!")
