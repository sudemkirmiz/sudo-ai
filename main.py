"""
Sudo AI — FastAPI Backend
Otonom Asistan'ın Client-Server mimarisi için REST API + SSE Streaming.
Gemini ve Ollama ReAct döngülerini içerir.
"""

import os
import json
import asyncio
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

# --- Proje içi modüller ---
from database import (
    get_db, 
    create_conversation, 
    list_conversations, 
    get_messages, 
    add_message,
    get_conversation,
    update_conversation_title,
    delete_conversation
)
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

# =====================================================
# FastAPI Uygulama Başlatma
# =====================================================

app = FastAPI(
    title="Sudo AI",
    description="Otonom Google Workspace Asistanı — Backend API",
    version="1.0.0"
)

# CORS — React frontend'in erişimi için
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# Araç Haritası & Sistem Promptu
# =====================================================

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


# =====================================================
# Ollama Araç Tanımları (JSON Schema)
# =====================================================

OLLAMA_TOOLS = [
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
            "description": "Google Drive'daki en son değiştirilen dosyaları listeler.",
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
                    "values": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}, "description": "Eklenecek veriler"}
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
            "description": "Gmail gelen kutusunu belirtilen sorguya göre tarar ve e-postaları listeler.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Gmail arama sorgusu (örn: 'is:unread'). Varsayılan: 'is:unread'"},
                    "max_results": {"type": "integer", "description": "Döndürülecek maksimum e-posta sayısı. Varsayılan: 5"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email_directly",
            "description": "Gmail üzerinden bir e-postayı doğrudan gönderir.",
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
            "description": "Google Takvim'deki yaklaşan etkinlikleri listeler.",
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
            "description": "Google Takvim'den belirtilen ID'ye sahip etkinliği siler.",
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
            "description": "Google Drive'dan belirtilen dosyayı çöp kutusuna taşır.",
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
            "description": "Google Drive'da bir dosyayı belirtilen klasöre taşır.",
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
            "description": "Mevcut bir Google Dokümanının sonuna metin ekler.",
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
            "description": "Google E-Tablolar'dan belirtilen aralıktaki verileri okur.",
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
            "description": "Mevcut bir Google Sunuları dosyasına yeni bir slayt sayfası ekler.",
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
            "description": "Google Drive'daki dosyaları türlerine göre filtreler ve listeler. file_type: 'slides', 'docs', 'sheets', 'folders', 'all'.",
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


# =====================================================
# Pydantic Modelleri (Request / Response)
# =====================================================

class ChatCreate(BaseModel):
    title: str = "Yeni Sohbet"

class MessageCreate(BaseModel):
    content: str
    provider: str = "gemini"              # "gemini" veya "ollama"
    model: Optional[str] = None           # Model adı (ör: "gemini-2.5-flash", "llama3.1")
    api_key: Optional[str] = None         # Gemini API key (opsiyonel, .env'den de okunabilir)
    ollama_host: str = "http://localhost:11434"


# =====================================================
# REST API Endpoints
# =====================================================

@app.get("/")
def root():
    return {"message": "Sudo AI Backend çalışıyor 🚀", "version": "1.0.0"}


@app.post("/api/chats")
def create_chat(body: ChatCreate, db: Session = Depends(get_db)):
    """Yeni boş bir sohbet oluşturur."""
    conv = create_conversation(db, title=body.title)
    return conv.to_dict()


@app.get("/api/chats")
def list_chats(db: Session = Depends(get_db)):
    """Geçmiş sohbetleri listeler (sol menü için)."""
    convs = list_conversations(db)
    return [c.to_dict() for c in convs]


@app.get("/api/chats/{chat_id}")
def get_chat_history(chat_id: str, db: Session = Depends(get_db)):
    """Seçilen sohbetin mesaj geçmişini getirir."""
    conv = get_conversation(db, chat_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Sohbet bulunamadı")
    
    msgs = get_messages(db, chat_id)
    return {
        "chat_id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "messages": [m.to_dict() for m in msgs]
    }


@app.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: str, db: Session = Depends(get_db)):
    """Belirtilen sohbeti ve tüm mesajlarını siler."""
    deleted = delete_conversation(db, chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sohbet bulunamadı")
    return {"message": "Sohbet silindi", "chat_id": chat_id}


# =====================================================
# Dosya Yükleme (RAG Context)
# =====================================================

from fastapi import File, UploadFile, Form

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    chat_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    PDF veya TXT dosyasını alır, metin içeriğini çıkarır ve
    sohbet bağlamına 'system' mesajı olarak ekler.
    """
    conv = get_conversation(db, chat_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Sohbet bulunamadı")

    filename = file.filename or "dosya"
    content_bytes = await file.read()

    # Metin çıkarma
    extracted_text = ""
    if filename.lower().endswith(".pdf"):
        try:
            import io
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(content_bytes))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            extracted_text = "\n".join(pages)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF okunamadı: {e}")
    elif filename.lower().endswith(".txt"):
        try:
            extracted_text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            extracted_text = content_bytes.decode("latin-1")
    else:
        raise HTTPException(status_code=400, detail="Sadece .pdf ve .txt dosyaları desteklenir.")

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Dosyadan metin çıkarılamadı.")

    # Metin çok uzunsa kırp (context window koruma)
    max_chars = 15000
    if len(extracted_text) > max_chars:
        extracted_text = extracted_text[:max_chars] + "\n\n[... metin kırpıldı ...]"

    # Bağlam olarak DB'ye ekle
    context_msg = f"[Sistem Notu: Kullanıcı '{filename}' dosyasını yükledi. Dosya içeriği aşağıdadır. Bu bilgiyi kullanıcının sorularını yanıtlamak için referans olarak kullan.]\n\n{extracted_text}"
    add_message(db, chat_id, "system", context_msg)

    return {
        "message": f"'{filename}' başarıyla yüklendi ve sohbet bağlamına eklendi.",
        "filename": filename,
        "char_count": len(extracted_text),
    }


# =====================================================
# Ajan ReAct Döngüsü — Gemini
# =====================================================

def run_gemini_agent(messages_history: list, api_key: str, model_name: str = "models/gemini-2.5-flash"):
    """
    Gemini ReAct döngüsünü çalıştırır.
    Araç çağrıları ve nihai metin cevabını yield eder.
    Her yield bir SSE event dict'idir.
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name=model_name,
        tools=list(available_tools.values()),
        system_instruction=SYSTEM_PROMPT
    )
    
    chat = model.start_chat(history=[])
    
    # Önceki mesajları chat'e yükle (son mesaj hariç — onu send_message ile göndereceğiz)
    # Gemini chat API'si Content nesneleri bekler, basitçe son kullanıcı mesajını gönderiyoruz
    # ve geçmiş bilgisini system prompt'a ek olarak ekliyoruz
    
    # Geçmişi context olarak ekle (son mesaj hariç)
    context_messages = messages_history[:-1]  # son mesaj prompt
    user_prompt = messages_history[-1]["content"]
    
    # Eğer geçmiş varsa, onu bir context string olarak prompt'a ekle
    if context_messages:
        history_text = "\n".join([
            f"{'Kullanıcı' if m['role'] == 'user' else 'Asistan'}: {m['content']}" 
            for m in context_messages 
            if m['role'] in ('user', 'assistant')
        ])
        if history_text:
            user_prompt = f"[Önceki sohbet geçmişi:\n{history_text}\n]\n\nKullanıcının yeni mesajı: {user_prompt}"
    
    try:
        response = chat.send_message(user_prompt)
        
        # Fonksiyon çağrısı var mı kontrol et
        fc = None
        if getattr(response, "parts", None):
            for part in response.parts:
                if getattr(part, "function_call", None):
                    fc = part.function_call
                    break
        
        if fc:
            func_name = fc.name
            args = dict(fc.args)
            
            yield {"event": "tool_call", "data": {"tool": func_name, "args": args, "step": 1}}
            
            if func_name in available_tools:
                tool_result = available_tools[func_name](**args)
                yield {"event": "tool_result", "data": {"tool": func_name, "result": str(tool_result)[:500]}}
                
                # Araç sonucunu modele geri gönder
                response = chat.send_message(
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
                yield {"event": "error", "data": {"message": f"Bilinmeyen araç: {func_name}"}}
        
        # Nihai metin cevabını al
        try:
            final_text = response.text
        except Exception:
            final_text = "İşlem tamamlandı."
        
        # Harf harf stream et
        for char in final_text:
            yield {"event": "token", "data": {"content": char}}
        
        yield {"event": "done", "data": {"full_content": final_text}}
        
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "Quota exceeded" in err_str:
            error_msg = "Gemini API kotanız doldu (Hata 429). Lütfen Ollama'yı seçerek yerel bir model kullanın."
        else:
            error_msg = f"Gemini hatası: {e}"
        yield {"event": "error", "data": {"message": error_msg}}


# =====================================================
# Ajan ReAct Döngüsü — Ollama
# =====================================================

def run_ollama_agent(messages_history: list, model_name: str = "llama3.1", ollama_host: str = "http://localhost:11434"):
    """
    Ollama ReAct while döngüsünü çalıştırır.
    Araç çağrıları ve nihai metin cevabını yield eder.
    """
    from ollama import Client
    client = Client(host=ollama_host)
    
    # Mesaj geçmişini Ollama formatına çevir
    messages = []
    messages.append({"role": "system", "content": SYSTEM_PROMPT})
    for m in messages_history:
        role = m["role"] if m["role"] in ["user", "assistant", "tool", "system"] else "user"
        messages.append({"role": role, "content": m["content"]})
    
    try:
        use_tools = model_name in ["gpt-oss:120b-cloud", "llama3.2", "llama3.1"]
        max_steps = 5
        step = 0
        final_text = ""
        
        while step < max_steps:
            step += 1
            kwargs = {"model": model_name, "messages": messages}
            if use_tools:
                kwargs["tools"] = OLLAMA_TOOLS
            
            response = client.chat(**kwargs)
            
            # Yanıttan mesajı ve tool_calls'ı güvenli şekilde çıkar
            resp_message = response.get('message', None) if isinstance(response, dict) else getattr(response, 'message', None)
            
            tool_calls = None
            if resp_message is not None:
                tool_calls = resp_message.get('tool_calls', None) if isinstance(resp_message, dict) else getattr(resp_message, 'tool_calls', None)
            
            # Araç çağrısı yoksa döngüden çık
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
                
                yield {"event": "tool_call", "data": {"tool": func_name, "args": args, "step": step}}
                
                if func_name in available_tools:
                    tool_result = available_tools[func_name](**args)
                    yield {"event": "tool_result", "data": {"tool": func_name, "result": str(tool_result)[:500]}}
                    
                    messages.append({
                        'role': 'tool',
                        'content': str(tool_result),
                        'name': func_name
                    })
                else:
                    yield {"event": "error", "data": {"message": f"Bilinmeyen araç: {func_name}"}}
                    messages.append({
                        'role': 'tool',
                        'content': f"Hata: {func_name} isimli araç bulunamadı.",
                        'name': func_name
                    })
        
        # Boş yanıt koruması
        if not final_text or final_text.strip() == '':
            messages.append({'role': 'user', 'content': 'Yukarıdaki araç sonuçlarını doğal bir dille özetle ve kullanıcıya bildir.'})
            retry_response = client.chat(model=model_name, messages=messages)
            rr_msg = retry_response.get('message', None) if isinstance(retry_response, dict) else getattr(retry_response, 'message', None)
            if rr_msg is not None:
                final_text = rr_msg.get('content', '') if isinstance(rr_msg, dict) else getattr(rr_msg, 'content', '')
            if not final_text or final_text.strip() == '':
                final_text = "İşlem tamamlandı."
        
        # Harf harf stream et
        for char in final_text:
            yield {"event": "token", "data": {"content": char}}
        
        yield {"event": "done", "data": {"full_content": final_text}}
        
    except Exception as e:
        err_str = str(e).lower()
        if "connection" in err_str or "connect" in err_str:
            error_msg = f"Ollama sunucusuna ({ollama_host}) bağlanılamadı. Lütfen URL'yi kontrol edin."
        elif "not found" in err_str or "404" in err_str:
            error_msg = f"'{model_name}' modeli sunucuda bulunamadı. `ollama pull {model_name}` komutunu çalıştırın."
        else:
            error_msg = f"Ollama hatası: {e}"
        yield {"event": "error", "data": {"message": error_msg}}


# =====================================================
# SSE Streaming Endpoint
# =====================================================

@app.post("/api/chats/{chat_id}/message")
def send_message(chat_id: str, body: MessageCreate, db: Session = Depends(get_db)):
    """
    Kullanıcı mesajını alır, DB'ye kaydeder, ajanı çalıştırır 
    ve SSE (Server-Sent Events) ile yanıt akışı döner.
    """
    # Sohbet var mı kontrol et
    conv = get_conversation(db, chat_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Sohbet bulunamadı")
    
    # Kullanıcı mesajını DB'ye kaydet
    add_message(db, chat_id, "user", body.content)
    
    # İlk mesajsa sohbet başlığını kullanıcı mesajından otomatik belirle
    existing_msgs = get_messages(db, chat_id)
    user_msgs = [m for m in existing_msgs if m.role == "user"]
    if len(user_msgs) == 1:
        # İlk kullanıcı mesajı — başlığı otomatik ayarla
        auto_title = body.content[:50] + ("..." if len(body.content) > 50 else "")
        update_conversation_title(db, chat_id, auto_title)
    
    # Mesaj geçmişini hazırla (DB'den)
    all_msgs = get_messages(db, chat_id)
    messages_history = [{"role": m.role, "content": m.content} for m in all_msgs]
    
    # Provider ve model ayarları
    provider = body.provider.lower()
    
    if provider == "gemini":
        api_key = body.api_key or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise HTTPException(status_code=400, detail="Gemini API anahtarı gerekli. Body'de 'api_key' gönderin veya .env'de GEMINI_API_KEY tanımlayın.")
        
        model_name = body.model or "models/gemini-2.5-flash"
        # Kısa model adlarını tam adlara çevir
        model_map = {
            "gemini-2.5-flash": "models/gemini-2.5-flash",
            "gemini-2.0-pro": "models/gemini-2.0-pro-exp-02-05",
            "gemini-1.5-flash": "models/gemini-1.5-flash",
        }
        model_name = model_map.get(model_name, model_name)
        
        agent_generator = run_gemini_agent(messages_history, api_key, model_name)
    
    elif provider == "ollama":
        model_name = body.model or "llama3.1"
        agent_generator = run_ollama_agent(messages_history, model_name, body.ollama_host)
    
    else:
        raise HTTPException(status_code=400, detail=f"Bilinmeyen provider: {provider}. 'gemini' veya 'ollama' kullanın.")
    
    # SSE stream oluştur
    def event_stream():
        full_content = ""
        for event in agent_generator:
            event_type = event["event"]
            event_data = json.dumps(event["data"], ensure_ascii=False)
            
            if event_type == "done":
                full_content = event["data"].get("full_content", full_content)
                # Asistan cevabını DB'ye kaydet
                db_session = next(get_db())
                try:
                    saved_msg = add_message(db_session, chat_id, "assistant", full_content)
                    event["data"]["message_id"] = saved_msg.id
                    event_data = json.dumps(event["data"], ensure_ascii=False)
                finally:
                    db_session.close()
            
            yield f"event: {event_type}\ndata: {event_data}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
