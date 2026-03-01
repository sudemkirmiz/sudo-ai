import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
import os
import io
import re
from dotenv import load_dotenv

load_dotenv()

# tools.py içinden fonksiyonlarımızı içe aktarıyoruz
from tools import (
    create_draft_email,
    Calendar,
    list_recent_drive_files,
    download_drive_file,
    read_google_docs,
    append_to_sheets,
    create_blank_slide,
    create_blank_document,
    read_emails,
    send_email_directly,
    list_calendar_events,
    delete_calendar_event,
    delete_drive_file,
    move_drive_file,
    write_to_google_doc,
    read_google_sheet,
    add_slide_to_presentation,
    list_drive_files_by_type
)

st.set_page_config(page_title="Otonom Asistan", page_icon="🤖", layout="wide")

# Özel CSS Tasarımı - Profesyonel Görünüm
st.markdown("""
<style>
    /* Streamlit varsayılan başlık ve alt bilgiyi gizler */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* header {visibility: hidden;} <- Yan menü açma/kapama butonunu da gizlediği için iptal edildi */
    
    /* Başlık için Google renklerine benzer havalı bir degrade (gradient) */
    h1 {
        font-family: 'Inter', sans-serif;
        background: -webkit-linear-gradient(45deg, #4285F4, #34A853, #FBBC05, #EA4335);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        padding-bottom: 10px;
    }
    
    /* Sohbet mesaj balonları için stil */
    [data-testid="stChatMessage"] {
        border-radius: 15px;
        padding: 10px 20px;
        margin-bottom: 15px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Sohbet giriş kutusu oval hatlar */
    [data-testid="stChatInput"] {
        border-radius: 25px !important;
        border: 1.5px solid #4285F4 !important;
    }
    
    /* Ses kayıt butonu ortalaması ve estetiği */
    [data-testid="stAudioRecorder"] {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Otonom Asistan")
st.markdown("*Google Workspace işlemlerinizi doğal dille asistanınıza yaptırın.*")

with st.expander("✨ Asistanın Yetenekleri"):
    st.markdown("""
    **Otonom Asistan — Tam CRUD Yetenekleri (18 Araç)**
    
    📧 **Gmail**
    - Gelen kutusunu sorgulama ve e-posta okuma
    - E-posta taslağı oluşturma
    - E-postayı doğrudan gönderme
    
    📅 **Google Calendar**
    - Takvime yeni etkinlik / toplantı ekleme
    - Yaklaşan etkinlikleri listeleme
    - Etkinlik silme / iptal etme
    
    📁 **Google Drive**
    - Son dosyaları listeleme
    - 🆕 **Türe göre akıllı listeleme** (slaytlar, dokümanlar, tablolar, klasörler)
    - Dosya indirme, silme ve klasörler arası taşıma
    
    📝 **Google Docs**
    - Yeni boş doküman oluşturma
    - Doküman içeriğini okuma
    - Mevcut dokümana metin ekleme
    
    📊 **Google Sheets**
    - Tablo verisini okuma
    - Tabloya yeni satır / veri ekleme
    
    🎞️ **Google Slides**
    - Yeni boş sunum oluşturma
    - Mevcut sunuma slayt ekleme
    
    🔄 **İnteraktif Seçim:** *"Slaytlarımı listele"* → Numaralı liste → *"1. dosyaya slayt ekle"* → Otomatik işlem!
    """)

available_tools = {
    "create_draft_email": create_draft_email,
    "Calendar": Calendar,
    "list_recent_drive_files": list_recent_drive_files,
    "download_drive_file": download_drive_file,
    "read_google_docs": read_google_docs,
    "append_to_sheets": append_to_sheets,
    "create_blank_slide": create_blank_slide,
    "create_blank_document": create_blank_document,
    "read_emails": read_emails,
    "send_email_directly": send_email_directly,
    "list_calendar_events": list_calendar_events,
    "delete_calendar_event": delete_calendar_event,
    "delete_drive_file": delete_drive_file,
    "move_drive_file": move_drive_file,
    "write_to_google_doc": write_to_google_doc,
    "read_google_sheet": read_google_sheet,
    "add_slide_to_presentation": add_slide_to_presentation,
    "list_drive_files_by_type": list_drive_files_by_type
}

SYSTEM_PROMPT = """Sen zeki, donanımlı ve yardımsever bir otonom asistansın. Birinci önceliğin kullanıcıyla doğal, akıcı ve mühendislik vizyonuna uygun bir dille sohbet etmektir.
KURAL 1: Kullanıcı sana hal hatır sorarsa, genel kültür/yazılım sorusu sorarsa veya sadece sohbet ediyorsa HİÇBİR ARACI (TOOL) ÇALIŞTIRMA. Sadece kendi bilgi birikiminle doğal bir yanıt ver.
KURAL 2: ARAÇLARI (Function Calling) SADECE VE SADECE kullanıcı açıkça bir işlem yapmanı isterse kullan. (Örn: Takvimime şunu ekle, mail at, dosya oluştur/oku dendiğinde).
KURAL 3: Bir aracı çalıştırdıktan sonra, bulduğun sonucu kullanıcıya mutlaka doğal ve nazik bir cümleyle özetle.
KURAL 4 (İNTERAKTİF SEÇİM VE GÖSTERİM): Dosya, etkinlik veya e-posta listeleme sonuçlarını kullanıcıya gösterirken ASLA ID'leri gösterme. Sonuçları MUTLAKA tıklanabilir Markdown linkleri olarak göster. Format: 1. [İsim](URL). Araç çıktısında '---[DAHİLİ BİLGİ]---' bölümündeki ID'leri kendi hafızanda tut ama kullanıcıya kesinlikle gösterme. Kullanıcı '1. dosyayı sil' veya '2. sunuma slayt ekle' dediğinde, hafızandaki ilgili ID'yi alıp doğrudan ilgili düzenleme aracını çalıştır.
KURAL 5 (LİNK FORMATI): Tüm araç sonuçlarındaki URL'leri kullanıcıya mutlaka Markdown link formatında ([metin](url)) ilet. Düz URL gösterme, her zaman [İsim](URL) formatını kullan.
YETENEKLER: Senin Gmail taslağı oluşturma/okuma/doğrudan gönderme, Google Takvim'e etkinlik ekleme/listeleme/silme, Drive erişimi (dosya listeleme/indirme/silme/taşıma/tür bazlı filtreleme), Docs okuma/oluşturma/yazma, Sheets okuma/veri ekleme ve Slides oluşturma/slayt ekleme yeteneklerin KESİNLİKLE VARDIR. Eğer kullanıcı çoklu bir işlem isterse (örn: belge oluştur ve mail at), araçlarını zincirleme (arka arkaya) kullan. Asla 'bunu yapamıyorum' veya 'bu yeteneğim yok' deme.
DÖNGÜ KURALI: Aynı aracı aynı parametrelerle arka arkaya birden fazla kez çağırma. Eğer bir işlem başarılıysa hemen sonucu kullanıcıya bildir."""

# --- YAN MENÜ (SIDEBAR) AYARLAR ---
st.sidebar.title("Ayarlar ⚙️")
provider = st.sidebar.radio("Zeka Sağlayıcısı Seçin:", ["Google Gemini (Bulut)", "Ollama (Yerel)"])

model_gemini = None
ollama_model = None

if provider == "Google Gemini (Bulut)":
    st.sidebar.markdown("### Gemini Ayarları")
    # Arayüzde sadece 3 model seçeneği sunuyoruz
    selected_model_display = st.sidebar.selectbox("Model Seçin:", [
        "gemini-2.5-flash (Varsayılan - Hızlı & Güncel)", 
        "gemini-2.0-pro-exp-02-05 (Gelişmiş Düşünme)", 
        "gemini-1.5-flash (Tam Stabilite)"
    ])
    
    # Kullanıcının seçtiği tam ekran adından, arka plandaki isme çeviriyoruz
    if "2.5" in selected_model_display:
        gemini_model_name = "models/gemini-2.5-flash"
    elif "2.0-pro" in selected_model_display:
        gemini_model_name = "models/gemini-2.0-pro-exp-02-05"
    else:
        gemini_model_name = "models/gemini-1.5-flash"
    
    # Ortam değişkeninde varsa varsayılan olarak getir, yoksa boş.
    default_api_key = os.getenv("GEMINI_API_KEY", "")
    gemini_api_key = st.sidebar.text_input("Gemini API Key:", value=default_api_key, type="password", help="API anahtarınızı buraya yapıştırın.")
    
    if not gemini_api_key:
        st.warning("Lütfen sol menüden Gemini API anahtarınızı girin veya Ollama'yı seçin.")
        st.stop()
    else:
        # API anahtarını çevre değişkenlerine geri yazıyoruz ki tools.py içindeki işlemler de okuyabilsin.
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        genai.configure(api_key=gemini_api_key)
        try:
            model_gemini = genai.GenerativeModel(
                model_name=gemini_model_name,
                tools=list(available_tools.values()),
                system_instruction=SYSTEM_PROMPT
            )
        except Exception as e:
            st.sidebar.error(f"Gemini modeli yüklenemedi: {e}")

elif provider == "Ollama (Yerel)":
    st.sidebar.markdown("### Ollama Ayarları")
    with st.sidebar.expander("⚙️ Gelişmiş Sunucu Ayarları"):
        ollama_host = st.text_input("Ollama Sunucu URL'si:", value="http://localhost:11434", help="Yerel veya uzak Ollama sunucu adresini (Cloud) girin.")
    ollama_model = st.sidebar.selectbox("Model Seçin:", ["gpt-oss:120b-cloud", "llama3.2", "llama3.1", "llama3"])
    st.info("Bilgi: 'gpt-oss:120b-cloud', 'llama3.2' ve 'llama3.1' modelleri araç kullanımını destekler.")

def process_audio(audio_bytes):
    """Ses baytlarını alır, SpeechRecognition ile metne çevirir."""
    recognizer = sr.Recognizer()
    try:
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="tr-TR")
            return text
    except sr.UnknownValueError:
        return "[HATA] Ses anlaşılamadı."
    except sr.RequestError as e:
        return f"[HATA] STT servisine bağlanılamadı: {e}"
    except Exception as e:
        return f"[HATA] Ses işlenirken bir sorun oluştu: {e}"

def convert_md_links_to_html(text):
    """
    Markdown linklerini ([metin](url)) HTML'e dönüştürür.
    Linklerin yeni sekmede açılmasını garanti eder (target=_blank).
    Dahili bilgi bloklarını kullanıcıdan gizler.
    """
    # Dahili bilgi bloklarını temizle
    text = re.sub(r'---\[DAHİLİ BİLGİ.*?$', '', text, flags=re.MULTILINE | re.DOTALL)
    # Markdown linklerini HTML'e çevir
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2" target="_blank">\1</a>',
        text
    )
    return text.strip()

# Session state (Geçmiş) hazırlığı
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    
if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = None

# Arayüzdeki mesajları listele
for msg in st.session_state.chat_history:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(convert_md_links_to_html(msg["content"]), unsafe_allow_html=True)

def handle_user_input(prompt):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("Düşünüyorum..."):
            final_text = ""
            try:
                if provider == "Google Gemini (Bulut)":
                    if st.session_state.gemini_chat is None:
                        st.session_state.gemini_chat = model_gemini.start_chat()
                    
                    response = st.session_state.gemini_chat.send_message(prompt)
                    
                    fc = None
                    if getattr(response, "parts", None):
                        for part in response.parts:
                            if getattr(part, "function_call", None):
                                fc = part.function_call
                                break
                    
                    if fc:
                        func_name = fc.name
                        args = dict(fc.args)
                        st.info(f"Gemini Araç Çağırıyor: {func_name} ...")
                        
                        if func_name in available_tools:
                            tool_result = available_tools[func_name](**args)
                            st.success(f"Araç Başarılı")
                            
                            response = st.session_state.gemini_chat.send_message(
                                genai.protos.Content(
                                    parts=[
                                        genai.protos.Part(
                                            function_response=genai.protos.FunctionResponse(
                                                name=func_name,
                                                response={"result": str(tool_result)} 
                                            )
                                        )
                                    ]
                                )
                            )
                        else:
                            st.error(f"Bilinmeyen araç: {func_name}")
                            
                    try:
                        final_text = response.text
                    except Exception:
                        final_text = "İşlem tamamlandı."
                    
                elif provider == "Ollama (Yerel)":
                    from ollama import Client
                    client = Client(host=ollama_host)
                    
                    # Ollama mesaj formatı: role ve content
                    messages = []
                    
                    for m in st.session_state.chat_history:
                        role = m["role"] if m["role"] in ["user", "assistant", "tool", "system"] else "user"
                        messages.append({"role": role, "content": m["content"]})
                        
                    # Python fonksiyonlarımızı Ollama'ya uyumlu araç listesi (JSON Schema) olarak tanıtıyoruz:
                    ollama_tools = [
                        {
                            "type": "function",
                            "function": {
                                "name": "create_draft_email",
                                "description": "Gmail üzerinden bir e-posta taslağı oluşturur.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "to_email": {"type": "string", "description": "Alıcı e-posta adresi"},
                                        "subject": {"type": "string", "description": "E-posta konusu"},
                                        "body_text": {"type": "string", "description": "E-posta içeriği"}
                                    },
                                    "required": ["to_email", "subject", "body_text"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "Calendar",
                                "description": "Google Takvim'e yeni bir etkinlik ekler.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "summary": {"type": "string", "description": "Etkinlik başlığı/özeti"},
                                        "start_time": {"type": "string", "description": "Başlangıç zamanı ISO 8601 formatında (örn. 2026-02-27T10:00:00+03:00)"},
                                        "end_time": {"type": "string", "description": "Bitiş zamanı ISO 8601 formatında"}
                                    },
                                    "required": ["summary", "start_time", "end_time"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_recent_drive_files",
                                "description": "Google Drive'daki en son değiştirilen dosyaları listeler. ALWAYS return items as clickable Markdown links: Format: 1. [Dosya Adı](URL). ID'leri kullanıcıya gösterme.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "limit": {"type": "integer", "description": "Listelenecek dosya sayısı (varsayılan: 5)"}
                                    }
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "download_drive_file",
                                "description": "Google Drive'dan belirtilen ID'li dosyayı bilgisayara indirir.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "file_id": {"type": "string", "description": "İndirilecek dosyanın Drive ID'si"},
                                        "file_name": {"type": "string", "description": "Bilgisayara kaydedilecek dosya adı (uzantısı ile)"}
                                    },
                                    "required": ["file_id", "file_name"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "read_google_docs",
                                "description": "Belirtilen Google Doküman (Docs) dosyasının metin içeriğini okur.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "document_id": {"type": "string", "description": "Okunacak dokümanın ID'si"}
                                    },
                                    "required": ["document_id"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "append_to_sheets",
                                "description": "Google E-Tablolar (Sheets) tablosuna yeni veri satırı ekler.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "spreadsheet_id": {"type": "string", "description": "Tablonun ID'si"},
                                        "range_name": {"type": "string", "description": "Sayfa ve veri aralığı (örn: 'Sayfa1!A:C')"},
                                        "values": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}, "description": "Eklenecek veriler (örn: [['Değer1', 'Değer2']])"}
                                    },
                                    "required": ["spreadsheet_id", "range_name", "values"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "create_blank_slide",
                                "description": "Yeni ve boş bir Google Sunular (Slides) dosyası oluşturur.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "presentation_title": {"type": "string", "description": "Sununun başlığı/adı"}
                                    },
                                    "required": ["presentation_title"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "create_blank_document",
                                "description": "Belirtilen başlıkla yeni bir boş Google Dokümanı (Docs) oluşturur.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string", "description": "Oluşturulacak dokümanın başlığı"}
                                    },
                                    "required": ["title"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "read_emails",
                                "description": "Gmail gelen kutusunu belirtilen sorguya göre tarar ve e-postaları listeler. ALWAYS return items as clickable Markdown links: Format: 1. [Konu](Gmail URL). Kullanıcı maillerini okumak, okunmamış mailleri görmek veya belirli bir kişiden gelen mailleri aramak istediğinde bu aracı kullan.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string", "description": "Gmail arama sorgusu (örn: 'is:unread', 'from:ali@test.com'). Varsayılan: 'is:unread'"},
                                        "max_results": {"type": "integer", "description": "Döndürülecek maksimum e-posta sayısı. Varsayılan: 5"}
                                    }
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "send_email_directly",
                                "description": "Gmail üzerinden bir e-postayı doğrudan gönderir (taslak oluşturmaz, anında iletir). Kullanıcı 'mail gönder', 'e-posta at', 'mesaj yolla' gibi ifadeler kullandığında bu aracı kullan.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "to": {"type": "string", "description": "Alıcı e-posta adresi"},
                                        "subject": {"type": "string", "description": "E-posta konusu"},
                                        "body": {"type": "string", "description": "E-posta gövde metni"}
                                    },
                                    "required": ["to", "subject", "body"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_calendar_events",
                                "description": "Google Takvim'deki yaklaşan etkinlikleri listeler. ALWAYS return items as clickable Markdown links: Format: 1. [Etkinlik Adı](Calendar URL). Bugünden itibaren belirtilen gün sayısı kadar ileriye bakar.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "days": {"type": "integer", "description": "Kaç gün ileriye bakılacağı. Varsayılan: 7"}
                                    }
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "delete_calendar_event",
                                "description": "Google Takvim'den belirtilen ID'ye sahip etkinliği siler. Kullanıcı bir etkinliği iptal etmek veya silmek istediğinde bu aracı kullan. Önce list_calendar_events ile etkinlik ID'sini bulman gerekebilir.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "event_id": {"type": "string", "description": "Silinecek etkinliğin benzersiz ID'si"}
                                    },
                                    "required": ["event_id"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "delete_drive_file",
                                "description": "Google Drive'dan belirtilen dosyayı çöp kutusuna taşır. Kullanıcı bir dosyayı silmek istediğinde bu aracı kullan. Önce list_recent_drive_files ile dosya ID'sini bulman gerekebilir.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "file_id": {"type": "string", "description": "Silinecek dosyanın Drive ID'si"}
                                    },
                                    "required": ["file_id"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "move_drive_file",
                                "description": "Google Drive'da bir dosyayı belirtilen klasöre taşır. Kullanıcı dosya taşımak veya düzenlemek istediğinde bu aracı kullan.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "file_id": {"type": "string", "description": "Taşınacak dosyanın Drive ID'si"},
                                        "folder_id": {"type": "string", "description": "Hedef klasörün Drive ID'si"}
                                    },
                                    "required": ["file_id", "folder_id"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "write_to_google_doc",
                                "description": "Mevcut bir Google Dokümanının sonuna metin ekler. Kullanıcı bir dokümana yazmak, not eklemek veya içerik güncellemek istediğinde bu aracı kullan.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "document_id": {"type": "string", "description": "Yazılacak dokümanın ID'si"},
                                        "text": {"type": "string", "description": "Dokümanın sonuna eklenecek metin"}
                                    },
                                    "required": ["document_id", "text"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "read_google_sheet",
                                "description": "Google E-Tablolar'dan (Sheets) belirtilen aralıktaki verileri okur ve döndürür. Kullanıcı tablo verilerini görmek, okumak veya kontrol etmek istediğinde bu aracı kullan.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "spreadsheet_id": {"type": "string", "description": "Tablonun ID'si"},
                                        "range_name": {"type": "string", "description": "Okunacak hücre aralığı (örn: 'Sayfa1!A1:C10')"}
                                    },
                                    "required": ["spreadsheet_id", "range_name"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "add_slide_to_presentation",
                                "description": "Mevcut bir Google Sunuları (Slides) dosyasına yeni bir slayt sayfası ekler ve başlık yazar. Kullanıcı sunuma sayfa/slayt eklemek istediğinde bu aracı kullan.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "presentation_id": {"type": "string", "description": "Sunumun ID'si"},
                                        "title_text": {"type": "string", "description": "Yeni slayda yazılacak başlık metni"}
                                    },
                                    "required": ["presentation_id", "title_text"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_drive_files_by_type",
                                "description": "Google Drive'daki dosyaları türlerine göre filtreler ve listeler. ALWAYS return items as clickable Markdown links: Format: 1. [Dosya Adı](URL). ID'leri kullanıcıya gösterme. Kullanıcı 'slaytlarımı listele', 'dokümanlarımı göster', 'tablolarımı getir' veya 'klasörlerimi göster' gibi ifadeler kullandığında bu aracı kullan. file_type: 'slides', 'docs', 'sheets', 'folders', 'all'.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "file_type": {"type": "string", "description": "Filtrelenecek dosya türü. Değerler: 'slides', 'docs', 'sheets', 'folders', 'all'. Varsayılan: 'all'"},
                                        "max_results": {"type": "integer", "description": "Listelenecek maksimum dosya sayısı. Varsayılan: 5"}
                                    }
                                }
                            }
                        }
                    ]
                    
                    try:
                        use_tools = ollama_model in ["gpt-oss:120b-cloud", "llama3.2", "llama3.1"]
                        max_steps = 5  # Sonsuz döngüı önlemek için maksimum araç adım sayısı
                        step = 0
                        
                        while step < max_steps:
                            step += 1
                            kwargs = {
                                "model": ollama_model,
                                "messages": messages
                            }
                            if use_tools:
                                kwargs["tools"] = ollama_tools
                            
                            response = client.chat(**kwargs)
                            
                            # Yanıttan mesajı ve tool_calls'ı güvenli şekilde çıkar
                            resp_message = response.get('message', None) if isinstance(response, dict) else getattr(response, 'message', None)
                            
                            tool_calls = None
                            if resp_message is not None:
                                tool_calls = resp_message.get('tool_calls', None) if isinstance(resp_message, dict) else getattr(resp_message, 'tool_calls', None)
                            
                            # Araç çağrısı yoksa döngüden çık (model nihai yanıt verdi)
                            if not tool_calls:
                                if resp_message is not None:
                                    final_text = resp_message.get('content', '') if isinstance(resp_message, dict) else getattr(resp_message, 'content', '')
                                else:
                                    final_text = "Model yanıt üretemedi."
                                break
                            
                            # Asistanın tool call isteğini mesaj geçmişine ekle
                            if isinstance(resp_message, dict):
                                messages.append(resp_message)
                            else:
                                messages.append({'role': 'assistant', 'content': '', 'tool_calls': tool_calls})
                            
                            # Araçları sırayla çalıştır
                            for tc in tool_calls:
                                if isinstance(tc, dict):
                                    func_name = tc['function']['name']
                                    args = tc['function']['arguments']
                                else:
                                    func_name = tc.function.name
                                    args = tc.function.arguments
                                    if not isinstance(args, dict):
                                        args = dict(args)
                                
                                st.info(f"Ollama Araç Çağırıyor ({step}. adım): {func_name} ...")
                                
                                if func_name in available_tools:
                                    tool_result = available_tools[func_name](**args)
                                    st.success(f"Araç Başarılı: {func_name}")
                                    
                                    messages.append({
                                        'role': 'tool',
                                        'content': str(tool_result),
                                        'name': func_name
                                    })
                                else:
                                    st.error(f"Bilinmeyen araç: {func_name}")
                                    messages.append({
                                        'role': 'tool',
                                        'content': f"Hata: {func_name} isimli araç bulunamadı.",
                                        'name': func_name
                                    })
                            
                            # Döngü devam eder: model tekrar çağrılır, 
                            # eğer yeni bir tool_call isterse zincirleme devam eder,
                            # istemezse nihai metni döndürür ve break ile çıkılır.
                        
                        # Boş yanıt koruması
                        if not final_text or final_text.strip() == '':
                            messages.append({'role': 'user', 'content': 'Yukarıdaki araç sonuçlarını doğal bir dille özetle ve kullanıcıya bildir.'})
                            retry_response = client.chat(model=ollama_model, messages=messages)
                            rr_msg = retry_response.get('message', None) if isinstance(retry_response, dict) else getattr(retry_response, 'message', None)
                            if rr_msg is not None:
                                final_text = rr_msg.get('content', '') if isinstance(rr_msg, dict) else getattr(rr_msg, 'content', '')
                            if not final_text or final_text.strip() == '':
                                final_text = "İşlem tamamlandı."
                                
                    except Exception as e:
                        err_str = str(e).lower()
                        if "connection" in err_str or "connect" in err_str:
                            final_text = f"[HATA] Ollama sunucusuna ({ollama_host}) bağlanılamadı veya sunucu aktif değil. Lütfen URL'yi kontrol edin."
                        elif "not found" in err_str or "404" in err_str:
                            final_text = f"[HATA] '{ollama_model}' modeli sunucuda bulunamadı.\n\nLütfen sunucu terminalinden şu komutu çalıştırarak modeli indirin:\n`ollama pull {ollama_model}`"
                        else:
                            final_text = f"[HATA] Ollama API çağrısı sırasında bir sorun meydana geldi: {e}"

                st.markdown(convert_md_links_to_html(final_text), unsafe_allow_html=True)
                st.session_state.chat_history.append({"role": "assistant", "content": final_text})
                
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "Quota exceeded" in err_str:
                    error_msg = "Gemini API kotanız doldu (Hata 429). Lütfen yan menüden Ollama'yı seçerek gpt-oss-120b veya yerel bir model kullanın."
                else:
                    error_msg = f"Bir hata oluştu: {e}"
                st.error(error_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})


# Input alanları
col1, col2 = st.columns([1, 10])

with col1:
    audio_bytes = audio_recorder(text="Ses", recording_color="#e8b62c", neutral_color="#6aa36f", icon_name="microphone", icon_size="2x")

with col2:
    text_input = st.chat_input("Mesajınızı yazın...")

if text_input:
    handle_user_input(text_input)

if audio_bytes:
    with st.spinner("Sesiniz metne çevriliyor..."):
        recognized_text = process_audio(audio_bytes)
        
    if recognized_text and not recognized_text.startswith("[HATA]"):
        st.info(f"🎙️ Algılanan Ses: *{recognized_text}*")
        handle_user_input(recognized_text)
    else:
        st.error(recognized_text)
