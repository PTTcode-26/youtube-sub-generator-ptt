import streamlit as st
from googletrans import Translator
import io
import zipfile
import time

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
    """Phân tích văn bản theo từng dòng để nhận diện TẤT CẢ các đoạn phụ đề SRT"""
    parsed_subs = []
    lines = text.split('\n')
    
    current_sub = None
    index = 1
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        if "-->" in line_str:
            if current_sub:
                parsed_subs.append(current_sub)
                index += 1
                
            start_time, end_time = line_str.split("-->")
            current_sub = {
                'index': index,
                'start': start_time.strip(),
                'end': end_time.strip(),
                'text_lines': []
            }
        elif line_str.isdigit() and not current_sub:
            continue
        elif current_sub:
            if line_str.isdigit() and lines[lines.index(line)+1 if lines.index(line)+1 < len(lines) else lines.index(line)].strip().find("-->") != -1:
                continue
            current_sub['text_lines'].append(line_str)
            
    if current_sub:
        parsed_subs.append(current_sub)
        
    final_subs = []
    for sub in parsed_subs:
        final_subs.append({
            'index': sub['index'],
            'start': sub['start'],
            'end': sub['end'],
            'text': " ".join(sub['text_lines']).strip()
        })
        
    return final_subs

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
            for _ in range(3):
                try:
                    translated_text = st.session_state.translator.translate(sub['text'], dest=target_lang).text
                    time.sleep(0.15)
                    break
                except Exception:
                    time.sleep(1)
            srt_content += f"{translated_text}\n\n"
    return srt_content

def translate_description(desc_text, target_lang='en'):
    """Dịch đoạn mô tả giới thiệu video"""
    if not desc_text.strip():
        return ""
    for _ in range(3):
        try:
            translated_desc = st.session_state.translator.translate(desc_text, dest=target_lang).text
            return translated_desc
        except Exception:
            time.sleep(1)
    return desc_text

# --- GIAO DIỆN ỨNG DỤNG WEB ---
st.set_page_config(page_title="YouTube Multi-Lang Subtitle & Desc Generator", page_icon="🎬", layout="centered")

st.title("🎬 Trình Tạo & Dịch Phụ Đề + Mô Tả YouTube")
st.write("Hệ thống hỗ trợ dịch hàng loạt cả **Phụ đề chuẩn SRT** và **Mô tả video** sang nhiều ngôn ngữ quốc tế.")

# Layout chia tab hoặc chia khu vực nhập liệu
st.subheader("1. Nhập dữ liệu gốc (Tiếng Việt)")

input_sub = st.text_area("✍️ [Khung 1] Nhập nội dung phụ đề gốc (.srt):", height=200, placeholder="00:00:39,800 --> 00:00:45,700\nNội dung câu thoại...")

input_desc = st.text_area("📝 [Khung 2] Nhập phần mô tả trên youtube:", height=150, placeholder="Ví dụ: Video này giới thiệu cảnh đẹp Bình Dương và Sài Gòn. Mời các bạn đón xem! Hãy nhớ Đăng ký kênh nhé...")

# Lựa chọn ngôn ngữ muốn dịch
st.subheader("🌐 2. Chọn ngôn ngữ muốn dịch sang:")
selected_langs = st.multiselect(
    "Mặc định luôn giữ lại file gốc. Chọn thêm các ngôn ngữ bạn muốn dịch:",
    options=list(LANGUAGES.keys()),
    format_func=lambda x: LANGUAGES[x],
    default=['en', 'ru', 'de', 'fr']
)

# Nút xử lý dữ liệu
if st.button("🚀 Bắt đầu dịch tự động hàng loạt", type="primary"):
    if not input_sub.strip() and not input_desc.strip():
        st.error("Vui lòng nhập ít nhất nội dung Phụ đề hoặc Mô tả video!")
    else:
        parsed_subs = parse_srt_input(input_sub) if input_sub.strip() else []
        
        if input_sub.strip() and not parsed_subs:
            st.error("Khung phụ đề nhập vào sai định dạng. Vui lòng kiểm tra lại ký tự mốc thời gian '-->'.")
        else:
            zip_buffer = io.BytesIO()
            description_results = f"=== MÔ TẢ GỐC (TIẾNG VIỆT) ===\n{input_desc}\n\n=================================\n\n"
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                # 1. Xử lý file gốc Tiếng Việt (nếu có nhập phụ đề)
                if parsed_subs:
                    vi_srt = generate_srt_string(parsed_subs, is_original=True)
                    zip_file.writestr("sub_Goc.srt", vi_srt)
                
                # 2. Xử lý các ngôn ngữ dịch thuật
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, lang_code in enumerate(selected_langs):
                    lang_display_name = LANGUAGES[lang_code].split(' ')[0]
                    status_text.text(f"⏳ Đang xử lý tiếng {lang_display_name}...")
                    
                    clean_lang_name = LANGUAGES[lang_code].split(' ')[1].replace('(', '').replace(')', '')
                    
                    # Dịch phụ đề
                    if parsed_subs:
                        lang_srt = generate_srt_string(parsed_subs, is_original=False, target_lang=lang_code)
                        zip_file.writestr(f"sub_{clean_lang_name}.srt", lang_srt)
                    
                    # Dịch mô tả
                    if input_desc.strip():
                        translated_desc = translate_description(input_desc, target_lang=lang_code)
                        description_results += f"=== MÔ TẢ TIẾNG {clean_lang_name.upper()} ===\n{translated_desc}\n\n=================================\n\n"
                    
                    progress_bar.progress((i + 1) / len(selected_langs))
                
                # Lưu file mô tả tổng hợp vào ZIP nếu người dùng có nhập mô tả
                if input_desc.strip():
                    zip_file.writestr("Mo_Ta_Da_Dich.txt", description_results)
                    
                status_text.text("✅ Đã xử lý xong tất cả nội dung!")
            
            st.success("🎉 Đã dịch và đóng gói thành công!")
            
            # Khung hiển thị trực quan phần mô tả đã dịch để copy nhanh không cần giải nén
            if input_desc.strip():
                with st.expander("📋 Xem nhanh và Copy phần Mô tả đã dịch tại đây"):
                    st.text_area("Nội dung mô tả đa ngôn ngữ:", value=description_results, height=250)
            
            st.download_button(
                label="📥 Tải Về Toàn Bộ File (.ZIP)",
                data=zip_buffer.getvalue(),
                file_name="phu_de_va_mo_ta_youtube.zip",
                mime="application/zip"
            )