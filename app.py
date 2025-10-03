import streamlit as st
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from PyPDF2 import PdfReader
import re
import os
import io
from datetime import datetime

# --- Memastikan Data NLTK Diunduh/Tersedia ---
# Menggunakan st.cache_resource untuk memastikan data NLTK hanya diunduh sekali.
# Logika ini menggantikan blok try-except/nltk.download di awal skrip.
@st.cache_resource
def download_nltk_data():
    try:
        # Download data yang sangat dibutuhkan NLTK
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        # Mengembalikan stopwords Bahasa Indonesia
        return set(stopwords.words('indonesian'))
    except LookupError:
        # Fallback jika gagal total (jarang terjadi setelah cache)
        return set()

STOPWORDS_ID = download_nltk_data()

# -------------------------------------------------------------------

# =================================================================
# FUNGSI UTILITAS 
# =================================================================

def save_summary_to_txt(summary, original_file_name, percentage):
    """
    Menyimpan string ringkasan ke file teks (.txt) dalam format bytes (untuk Streamlit download).
    """
    # Header TXT yang rapi
    header = "="*60 + "\n"
    header += "RINGKASAN MATERI EDUKASI OTOMATIS\n"
    header += "="*60 + "\n"
    header += f"File Sumber        : {original_file_name}\n"
    header += f"Persentase Ringkasan: {int(percentage*100)}%\n"
    header += f"Tanggal Pembuatan  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += "-"*60 + "\n\n"
    
    formatted_summary = summary.replace('. ', '.\n\n') 
    
    full_content = header + formatted_summary
    
    return full_content.encode('utf-8')


def extract_text_from_pdf(uploaded_file):
    """Mengekstrak teks dari file PDF yang diunggah Streamlit."""
    text = ""
    try:
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    except Exception as e:
        st.error(f"Error saat membaca PDF: {e}")
        return None
    return text.strip()


def perform_summarization(text, percentage=0.3):
    """Logika Peringkasan Ekstraktif (Sama seperti sebelumnya)"""
    if not text:
        return None
    
    cleaned_text = re.sub(r'\s+', ' ', text).strip()
    sentences = sent_tokenize(cleaned_text)
    words = word_tokenize(cleaned_text.lower())
    
    word_frequencies = {}
    for word in words:
        word = re.sub(r'[^a-zA-Z]', '', word) 
        if word not in STOPWORDS_ID and len(word) > 1:
            word_frequencies[word] = word_frequencies.get(word, 0) + 1

    if not word_frequencies:
        return "Teks terlalu pendek atau tidak relevan untuk diringkas."
        
    maximum_frequency = max(word_frequencies.values())
    for word in word_frequencies:
        word_frequencies[word] = (word_frequencies[word] / maximum_frequency)

    sentence_scores = {}
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            word = re.sub(r'[^a-zA-Z]', '', word)
            if word in word_frequencies:
                sentence_scores[sentence] = sentence_scores.get(sentence, 0) + word_frequencies[word]
    
    num_sentences = int(len(sentences) * percentage)
    
    scored_sentences_with_index = []
    for i, sentence in enumerate(sentences):
        score = sentence_scores.get(sentence, 0)
        scored_sentences_with_index.append((score, sentence, i))
    
    best_sentences = sorted(scored_sentences_with_index, key=lambda item: item[0], reverse=True)
    selected_sentences = best_sentences[:num_sentences]
    final_summary_list = sorted(selected_sentences, key=lambda item: item[2])
    
    final_summary = " ".join([sent for score, sent, index in final_summary_list])

    return final_summary


# =================================================================
# FUNGSI UTAMA STREAMLIT
# =================================================================

def main():
    st.set_page_config(page_title="Ringkasan Edukasi Python AI", layout="centered")
    st.title("📚 Ringkasan Materi Edukasi Otomatis")
    st.markdown("Aplikasi web untuk merangkum file PDF/Teks menggunakan Algoritma Ekstraktif (Python NLP).")

    # --- Sidebar Kontrol ---
    st.sidebar.header("⚙️ Pengaturan Ringkasan")
    
    percentage = st.sidebar.slider(
        "Persentase Ringkasan (%)", 
        min_value=10, max_value=50, value=25, step=5
    ) / 100
    
    st.sidebar.info("Persentase 25% adalah rasio yang baik untuk ringkasan cepat.")
    
    # --- Input Utama ---
    tab1, tab2 = st.tabs(["Unggah File (PDF/TXT)", "Input Teks Langsung"])

    raw_text = None
    file_name = "Teks_Manual"
    uploaded_file = None
    
    with tab1:
        uploaded_file = st.file_uploader("Unggah File Materi", type=["pdf", "txt"])
        
        if uploaded_file is not None:
            file_name = uploaded_file.name
            
            # Membaca file
            if file_name.lower().endswith('.pdf'):
                raw_text = extract_text_from_pdf(uploaded_file)
            elif file_name.lower().endswith('.txt'):
                raw_text = uploaded_file.read().decode('utf-8')
    
    with tab2:
        manual_text = st.text_area("Atau Tempel Teks di Sini", height=300)
        if manual_text:
            raw_text = manual_text
            file_name = "Teks_Langsung"


    # --- Peringkasan dan Output ---
    if raw_text:
        st.subheader("Hasil Ringkasan Otomatis")
        
        # Jalankan Peringkasan
        with st.spinner('Sedang merangkum teks...'):
            summary = perform_summarization(raw_text, percentage)

        if summary and "Error" not in summary:
            st.success("Ringkasan Berhasil Dibuat!")
            
            # Tampilkan Ringkasan di Web
            st.markdown(summary.replace('. ', '.\n\n'))
            
            st.markdown("---")
            st.subheader("📥 Unduh Hasil")
            
            # 2. Unduh TXT
            txt_bytes = save_summary_to_txt(summary, file_name, percentage)
            txt_output_name = f"{os.path.splitext(file_name)[0]}_RINGKASAN_{int(percentage*100)}persen.txt"
            st.download_button(
                label="Unduh sebagai TXT 📝",
                data=txt_bytes,
                file_name=txt_output_name,
                mime="text/plain"
            )

        elif "Error" in summary:
             st.error(summary)
        
    elif uploaded_file is None and not st.session_state.get('manual_text_active', False):
         st.info("Silakan unggah file atau tempel teks pada tab di atas untuk memulai.")

if __name__ == '__main__':
    main()
