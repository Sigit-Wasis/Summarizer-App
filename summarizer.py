import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from PyPDF2 import PdfReader
import re

# Kata kunci penting: Sesuaikan ke bahasa yang Anda gunakan (misalnya Indonesian)
STOPWORDS_ID = set(stopwords.words('indonesian'))

def extract_text_from_file(file_path):
    """Mengekstrak teks dari file, mendukung PDF."""
    if file_path.lower().endswith('.pdf'):
        text = ""
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text()
        except Exception as e:
            return f"Error membaca PDF: {e}"
        return text
    
    elif file_path.lower().endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    else:
        return file_path 


def perform_summarization(text, percentage=0.3):
    """Melakukan ringkasan ekstraktif berdasarkan frekuensi kata."""
    if not text or "Error" in text:
        return text

    sentences = sent_tokenize(text)
    words = word_tokenize(text.lower())
    
    word_frequencies = {}
    for word in words:
        word = re.sub(r'[^a-zA-Z]', '', word) 
        if word not in STOPWORDS_ID and len(word) > 1:
            word_frequencies[word] = word_frequencies.get(word, 0) + 1

    if not word_frequencies:
        return "Teks terlalu pendek atau tidak relevan untuk diringkas."
        
    maximum_frequency = max(word_frequencies.values())
    for word in word_frequencies:
        word_frequencies[word] /= maximum_frequency

    sentence_scores = {}
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            word = re.sub(r'[^a-zA-Z]', '', word)
            if word in word_frequencies:
                sentence_scores[sentence] = sentence_scores.get(sentence, 0) + word_frequencies[word]
    
    num_sentences = int(len(sentences) * percentage)
    
    scored_sentences = sorted(
        [(score, sentence) for sentence, score in sentence_scores.items()], 
        key=lambda item: item[0], reverse=True
    )
    
    best_sentences = scored_sentences[:num_sentences]
    final_summary = " ".join([sent for score, sent in sorted(best_sentences, key=lambda item: sentences.index(item[1]))])

    return final_summary


def save_summary_to_file(original_text, summary_text, output_path="ringkasan_output.txt"):
    """Menyimpan hasil ringkasan ke file .txt dengan perbandingan kata."""
    try:
        total_kata_asli = len(word_tokenize(original_text))
        total_kata_ringkasan = len(word_tokenize(summary_text))

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("===== HASIL RINGKASAN =====\n\n")
            f.write(summary_text.strip())
            f.write("\n\n===== STATISTIK =====\n")
            f.write(f"Total kata asli     : {total_kata_asli}\n")
            f.write(f"Total kata ringkasan: {total_kata_ringkasan}\n")
            f.write(f"Persentase ringkasan: {round((total_kata_ringkasan/total_kata_asli)*100,2)}%\n")
            f.write("\n===== SELESAI =====")
        return f"Ringkasan berhasil disimpan di {output_path}"
    except Exception as e:
        return f"Gagal menyimpan file: {e}"


# --- Contoh Penggunaan ---
if __name__ == '__main__':
    FILE_PATH = "sample_materi.txt" 
    RINGKASAN_PERSENTASE = 0.25 # 25% dari teks asli

    print(f"Mengambil teks dari: {FILE_PATH}")
    raw_text = extract_text_from_file(FILE_PATH)
    
    if raw_text:
        summary = perform_summarization(raw_text, RINGKASAN_PERSENTASE)
        
        print("\n" + "="*50)
        print("HASIL RINGKASAN:")
        print("="*50)
        print(summary)
        print("="*50)

        result = save_summary_to_file(raw_text, summary, "ringkasan_sample.txt")
        print(result)
