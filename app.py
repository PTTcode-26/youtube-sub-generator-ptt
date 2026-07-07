import streamlit as st
from googletrans import Translator
import io
import zipfile
import time
import re

# Cấu hình danh sách ngôn ngữ dịch thuật đầy đủ
LANGUAGES = {
    'en': 'Tiếng Anh (English)',
    'hi': 'Tiếng Hindi (हिन्दी)',
    'ru': 'Tiếng Nga (Русский)',
    'de': 'Tiếng Đức (Deutsch)',
    'fr': 'Tiếng Pháp (Français)',
    'ja': 'Tiếng Nhật (日本語)',
    'ko': 'Tiếng Hàn (한국어)',
    'zh-cn': 'Tiếng Trung (简体中文)',
    'es': 'Tiếng Tây Ban Nha (Español)',
    'ar': 'Tiếng Ả Rập (العربية)',
    'nl': 'Tiếng Hà Lan (Nederlands)',
    'fi': 'Tiếng Phần Lan (Suomi)',
    'it': 'Tiếng Ý (Italiano)',
    'tl': 'Tiếng Philippines (Tagalog)',
    'el': 'Tiếng Hy Lạp (Ελληνικά)',
    'iw': 'Tiếng Do Thái (Hebrew)'
}

if 'translator' not in st.session_state:
    st.session_state.translator = Translator()

def parse_srt_input(text):
    """Phân tích văn bản nhập vào theo định dạng chuẩn SRT"""
    parsed_subs = []
    # Chia tách theo các khối dòng trống
    blocks = re.split(r'\n\s*\n', text.strip())
    index = 1
    
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
            
        time_line = ""
        text_lines = []
        
        # Kiểm tra xem dòng đầu tiên có phải là số thứ tự không
        if lines[0].isdigit():
            if len(lines) > 1 and "-->" in lines[1]:
                time_line = lines[1]
                text_lines = lines[2:]
        elif "-->" in lines[0]:
            time_line = lines[0]
            text_lines = lines[1:]
            
        if time_line and "-->" in time_line:
            start_time, end_time = time_line.split("-->")
            sub_text = " ".join(text_lines)
            
            parsed_subs.append({
                'index': index,
                'start': start_time.strip(),
                'end': end_time.strip(),
                'text': sub_text
            })
            index += 1
            
    return parsed_subs

def generate_srt_string(subs_data, is_original=True, target_lang='en'):
    """Tạo nội dung file SRT từ cấu trúc dữ liệu"""
    srt_content = ""
    for sub in subs_data:
        srt_content += f"{sub['index']}\n"
        srt_content += f"{sub['start']} --> {sub['end']}\n"
        
        if is_original:
            srt_content += f"{sub['text']}\n\n"
        else:
            if not sub['text']:
                srt_content += "\n\n"
                continue
                
            translated_text = sub['text']
            for _ in range(3):  # Thử lại tối đa 3 lần nếu lỗi mạng
                try:
                    translated_text = st.session_state.translator.translate(sub['text'], dest=target_lang).text
                    time.sleep(0.2)  # Tránh bị Google quét spam
                    break
                except Exception:
                    time.sleep(1)
            srt_content += f"{translated_text}\n\n"
    return srt_content

# --- GIAO DIỆN ỨNG DỤNG WEB ---
st.set_page_config(page_title="YouTube Multi-Lang Subtitle Generator", page_icon="🎬", layout="centered")

st.title("🎬 Trình Tạo & Dịch Phụ Đề YouTube")
st.write("Nhập phụ đề gốc theo chuẩn định dạng `.srt`, hệ thống sẽ tự động dịch hàng loạt sang nhiều ngôn ngữ quốc tế.")

# Hướng dẫn mẫu
with st.expander("💡 Xem định dạng mẫu để nhập dữ liệu"):
    st.code(
        "00:00:39,800 --> 00:00:45,700\n"
        "Xin chào mọi người, hiện tại mình đang ở Bình Dương, nơi này cách Sài Gòn khoảng 50km\n\n"
        "00:00:46,000 --> 00:00:52,100\n"
        "Hôm nay mình sẽ dẫn mọi người đi tham quan một địa điểm rất đẹp.",
        language="text"
    )

# Khung nhập dữ liệu
input_data = st.text_area("✍️ Nhập nội dung phụ đề gốc của bạn tại đây:", height=250, placeholder="00:00:00,000 --> 00:00:05,000\nNội dung câu thoại...")

# Lựa chọn ngôn ngữ muốn dịch
st.subheader("🌐 Chọn ngôn ngữ muốn dịch sang:")
selected_langs = st.multiselect(
    "Mặc định luôn có file gốc. Chọn thêm các ngôn ngữ bạn muốn dịch:",
    options=list(LANGUAGES.keys()),
    format_func=lambda x: LANGUAGES[x],
    default=['en', 'ru', 'de', 'fr']  # Đặt mặc định chọn sẵn một số ngôn ngữ phổ biến
)

# Nút xử lý dữ liệu
if st.button("🚀 Bắt đầu dịch phụ đề hàng loạt", type="primary"):
    if not input_data.strip():
        st.error("Vui lòng nhập nội dung phụ đề trước khi bấm nút!")
    else:
        parsed_subs = parse_srt_input(input_data)
        
        if not parsed_subs:
            st.error("Dữ liệu nhập vào sai định dạng. Vui lòng kiểm tra lại cấu trúc mốc thời gian '-->'.")
        else:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                # 1. Tạo file Tiếng Việt gốc
                vi_srt = generate_srt_string(parsed_subs, is_original=True)
                zip_file.writestr("sub_Goc.srt", vi_srt)
                
                # 2. Tạo các file dịch thuật
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, lang_code in enumerate(selected_langs):
                    lang_display_name = LANGUAGES[lang_code].split(' ')[0]
                    status_text.text(f"⏳ Đang dịch sang {lang_display_name}...")
                    
                    lang_srt = generate_srt_string(parsed_subs, is_original=False, target_lang=lang_code)
                    
                    clean_lang_name = LANGUAGES[lang_code].split(' ')[1].replace('(', '').replace(')', '')
                    file_name = f"sub_{clean_lang_name}.srt"
                    zip_file.writestr(file_name, lang_srt)
                    
                    progress_bar.progress((i + 1) / len(selected_langs))
                
                status_text.text("✅ Đã xử lý xong tất cả ngôn ngữ!")
            
            st.success("🎉 Đã dịch và tạo file phụ đề thành công!")
            
            st.download_button(
                label="📥 Tải Về Toàn Bộ File (.ZIP)",
                data=zip_buffer.getvalue(),
                file_name="phu_de_youtube_da_dich.zip",
                mime="application/zip"
            )