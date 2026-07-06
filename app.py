import streamlit as st
from googletrans import Translator
import io
import zipfile

# Cấu hình danh sách ngôn ngữ dịch thuật (Đã thêm tiếng Hindi)
LANGUAGES = {
    'en': 'Tiếng Anh (English)',
    'hi': 'Tiếng Hindi (हिन्दी)',
    'ja': 'Tiếng Nhật (日本語)',
    'ko': 'Tiếng Hàn (한국어)',
    'zh-cn': 'Tiếng Trung (简体中文)',
    'es': 'Tiếng Tây Ban Nha (Español)',
    'fr': 'Tiếng Pháp (Français)'
}

translator = Translator()

def convert_to_srt_time(time_str):
    """Chuyển đổi dạng '00:01' hoặc '01:23' thành chuẩn SRT '00:00:01,000'"""
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 2:
            return f"00:{parts[0]}:{parts[1]},000"
        elif len(parts) == 3:
            return f"{parts[0]}:{parts[1]}:{parts[2]},000"
    except Exception:
        pass
    return "00:00:00,000"

def parse_input_text(text):
    """Phân tích văn bản nhập vào thành cấu trúc dữ liệu phụ đề"""
    parsed_subs = []
    index = 1
    lines = text.strip().split('\n')
    
    for line in lines:
        if '|' in line and '-' in line:
            try:
                time_part, text_part = line.split('|', 1)
                start_time, end_time = time_part.split('-')
                
                parsed_subs.append({
                    'index': index,
                    'start': convert_to_srt_time(start_time),
                    'end': convert_to_srt_time(end_time),
                    'text': text_part.strip()
                })
                index += 1
            except Exception:
                continue
    return parsed_subs

def generate_srt_string(subs_data, is_original=True, target_lang='en'):
    """Tạo nội dung file SRT dưới dạng chuỗi văn bản"""
    srt_content = ""
    for sub in subs_data:
        srt_content += f"{sub['index']}\n"
        srt_content += f"{sub['start']} --> {sub['end']}\n"
        
        if is_original:
            srt_content += f"{sub['text']}\n\n"
        else:
            try:
                translated_text = translator.translate(sub['text'], dest=target_lang).text
                srt_content += f"{translated_text}\n\n"
            except Exception:
                srt_content += f"{sub['text']}\n\n" # Giữ nguyên gốc nếu lỗi mạng
    return srt_content

# --- GIAO DIỆN ỨNG DỤNG WEB ---
st.set_page_config(page_title="YouTube Multi-Lang Subtitle Generator", page_icon="📝", layout="centered")

st.title("🎬 Trình Tạo & Dịch Phụ Đề YouTube")
st.write("Nhập mốc thời gian và chú thích tiếng Việt, hệ thống sẽ tự động dịch hàng loạt ra các file `.srt` để bạn upload lên YouTube.")

# Hướng dẫn mẫu
with st.expander("💡 Xem định dạng mẫu để nhập dữ liệu"):
    st.code(
        "00:01 - 00:05 | Bình minh trên đỉnh Fansipan với biển mây bồng bềnh.\n"
        "00:06 - 00:12 | Ánh nắng đầu ngày len lỏi qua các thung lũng.\n"
        "00:15 - 00:20 | Đây là điểm đến không thể bỏ qua khi tới Sa Pa.",
        language="text"
    )

# Khung nhập dữ liệu
input_data = st.text_area("✍️ Nhập nội dung chú thích của bạn tại đây:", height=250, placeholder="Thời gian bắt đầu - Thời gian kết thúc | Nội dung chú thích")

# Lựa chọn ngôn ngữ muốn dịch
st.subheader("🌐 Chọn ngôn ngữ muốn dịch sang:")
selected_langs = st.multiselect(
    "Mặc định sẽ luôn có file Tiếng Việt gốc. Chọn thêm các ngôn ngữ khác:",
    options=list(LANGUAGES.keys()),
    format_func=lambda x: LANGUAGES[x],
    default=['en', 'hi', 'ja'] # Đặt mặc định chọn sẵn Anh, Hindi, Nhật
)

# Nút xử lý dữ liệu
if st.button("🚀 Bắt đầu tạo và dịch phụ đề", type="primary"):
    if not input_data.strip():
        st.error("Vui lòng nhập nội dung phụ đề trước khi bấm nút!")
    else:
        parsed_subs = parse_input_text(input_data)
        
        if not parsed_subs:
            st.error("Dữ liệu nhập vào sai định dạng. Vui lòng kiểm tra lại (Thiếu dấu '-' hoặc '|').")
        else:
            # Tạo file ZIP trong bộ nhớ để người dùng tải về toàn bộ file 1 lần
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                # 1. Tạo file Tiếng Việt gốc
                vi_srt = generate_srt_string(parsed_subs, is_original=True)
                zip_file.writestr("sub_Tieng_Viet.srt", vi_srt)
                
                # 2. Tạo các file dịch thuật
                progress_bar = st.progress(0)
                for i, lang_code in enumerate(selected_langs):
                    # Cập nhật thanh tiến trình
                    progress_bar.progress((i + 1) / len(selected_langs))
                    
                    lang_srt = generate_srt_string(parsed_subs, is_original=False, target_lang=lang_code)
                    # Lấy tên tiếng Việt không dấu hoặc dạng ngắn gọn để đặt tên file
                    clean_lang_name = LANGUAGES[lang_code].split(' ')[1].replace('(', '').replace(')', '')
                    file_name = f"sub_{clean_lang_name}.srt"
                    zip_file.writestr(file_name, lang_srt)
            
            st.success("🎉 Đã dịch và tạo file phụ đề thành công!")
            
            # Nút tải file ZIP về máy
            st.download_button(
                label="📥 Tải Về Toàn Bộ File (.ZIP)",
                data=zip_buffer.getvalue(),
                file_name="phu_de_youtube.zip",
                mime="application/zip"
            )