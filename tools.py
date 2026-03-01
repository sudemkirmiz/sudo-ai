import base64
import datetime
from email.message import EmailMessage

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from auth import authenticate_google

def create_draft_email(to_email, subject, body_text):
    """
    Gmail API kullanarak belirtilen adrese, konu ve içerikle
    bir e-posta taslağı oluşturur.
    """
    try:
        creds = authenticate_google()
        service = build('gmail', 'v1', credentials=creds)
        
        message = EmailMessage()
        message.set_content(body_text)
        message['To'] = to_email
        message['Subject'] = subject
        
        # Mesajı Base64 URL-safe formatına çeviriyoruz
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'message': {'raw': encoded_message}}
        
        draft = service.users().drafts().create(userId='me', body=create_message).execute()
        draft_id = draft['id']
        gmail_link = f"https://mail.google.com/mail/u/0/#drafts"
        return f"[BAŞARILI] E-posta taslağı başarıyla oluşturuldu.\nTaslak ID: {draft_id}\n🔗 Taslakları görüntüle: {gmail_link}"
    except Exception as e:
        return f"[HATA] E-posta taslağı oluşturulurken bir sorun meydana geldi: {e}"

def Calendar(summary, start_time, end_time):
    """
    Google Calendar API kullanarak kullanıcının 'primary' (birincil)
    takvimine etkinlik ekler.
    Tarihlerin ISO 8601 (örn. 2026-02-27T10:00:00+03:00) formatında olması beklenir.
    """
    try:
        creds = authenticate_google()
        service = build('calendar', 'v3', credentials=creds)
        
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time,
            },
            'end': {
                'dateTime': end_time,
            },
        }
        
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        event_link = event_result.get('htmlLink', 'https://calendar.google.com')
        return f"[BAŞARILI] Etkinlik takvime eklendi.\n🔗 Etkinliği görüntüle: {event_link}"
    except Exception as e:
        return f"[HATA] Takvime etkinlik eklenirken bir sorun meydana geldi: {e}"

def list_recent_drive_files(limit=5):
    """
    Google Drive API kullanarak son değiştirilen dosyaların
    adını, linkini ve ID'sini çeker (varsayılan: 5 dosya).
    """
    try:
        creds = authenticate_google()
        service = build('drive', 'v3', credentials=creds)
        
        results = service.files().list(
            pageSize=limit,
            fields="files(id, name, mimeType, webViewLink)",
            orderBy="modifiedTime desc"
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            return "[BİLGİ] Drive üzerinde listelenecek yeni dosya bulunamadı."
        
        output = f"[BAŞARILI] Drive'daki son {limit} dosya:\n\n"
        for i, item in enumerate(items, 1):
            link = item.get('webViewLink', f"https://drive.google.com/file/d/{item['id']}/view")
            output += f"  {i}. [{item['name']}]({link})\n"

        output += "\n---[DAHİLİ BİLGİ - KULLANICIYA GÖSTERME]---\n"
        for i, item in enumerate(items, 1):
            output += f"{i}={item['id']}\n"
            
        return output
    except Exception as e:
        return f"[HATA] Drive dosyaları alınırken bir sorun meydana geldi: {e}"

def list_drive_files_by_type(file_type="all", max_results=5):
    """
    Google Drive API kullanarak belirtilen dosya türüne göre filtreleyerek
    dosyaları listeler. file_type parametresine göre MIME Type filtresi uygular.
    Desteklenen türler: 'slides', 'docs', 'sheets', 'folders', 'all'.
    Döndürdüğü listede her dosyanın adı ve ID'si bulunur.
    """
    try:
        creds = authenticate_google()
        service = build('drive', 'v3', credentials=creds)

        mime_map = {
            "slides": "application/vnd.google-apps.presentation",
            "docs": "application/vnd.google-apps.document",
            "sheets": "application/vnd.google-apps.spreadsheet",
            "folders": "application/vnd.google-apps.folder",
        }

        query_parts = ["trashed = false"]
        if file_type.lower() in mime_map:
            mime = mime_map[file_type.lower()]
            query_parts.append(f"mimeType='{mime}'")

        q = " and ".join(query_parts)

        results = service.files().list(
            pageSize=max_results,
            fields="files(id, name, mimeType)",
            orderBy="modifiedTime desc",
            q=q
        ).execute()

        items = results.get('files', [])

        type_labels = {
            "slides": "Sunum (Slides)",
            "docs": "Doküman (Docs)",
            "sheets": "E-Tablo (Sheets)",
            "folders": "Klasör",
            "all": "Tüm Dosya",
        }
        label = type_labels.get(file_type.lower(), file_type)

        if not items:
            return f"[BİLGİ] Drive'da '{label}' türünde dosya bulunamadı."

        # MIME type'a göre doğru Google Workspace linkini oluştur
        link_map = {
            "application/vnd.google-apps.document": "https://docs.google.com/document/d/{}/edit",
            "application/vnd.google-apps.spreadsheet": "https://docs.google.com/spreadsheets/d/{}/edit",
            "application/vnd.google-apps.presentation": "https://docs.google.com/presentation/d/{}/edit",
            "application/vnd.google-apps.folder": "https://drive.google.com/drive/folders/{}",
        }
        default_link = "https://drive.google.com/file/d/{}/view"

        output = f"[BAŞARILI] Drive'daki {label} dosyaları ({len(items)} adet):\n\n"
        for i, item in enumerate(items, 1):
            mime = item.get('mimeType', '')
            link = link_map.get(mime, default_link).format(item['id'])
            output += f"  {i}. [{item['name']}]({link})\n"

        output += "\n---[DAHİLİ BİLGİ - KULLANICIYA GÖSTERME]---\n"
        for i, item in enumerate(items, 1):
            output += f"{i}={item['id']}\n"

        return output
    except Exception as e:
        return f"[HATA] Drive dosyaları listelenirken bir sorun meydana geldi: {e}"

def download_drive_file(file_id, file_name):
    """
    Belirtilen ID'ye sahip dosyayı bilgisayara indirir.
    """
    try:
        creds = authenticate_google()
        service = build('drive', 'v3', credentials=creds)
        
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_name, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        return f"[BAŞARILI] '{file_name}' adlı dosya bilgisayarınıza indirildi."
    except Exception as e:
        return f"[HATA] Dosya indirilirken bir sorun meydana geldi: {e}"

def read_google_docs(document_id):
    """
    Belirtilen Google Docs belgesinin içindeki metni okur ve döndürür.
    """
    try:
        creds = authenticate_google()
        service = build('docs', 'v1', credentials=creds)
        
        document = service.documents().get(documentId=document_id).execute()
        content = document.get('body').get('content')
        text = ""
        for element in content:
            if 'paragraph' in element:
                elements = element.get('paragraph').get('elements')
                for elem in elements:
                    text += elem.get('textRun').get('content') if 'textRun' in elem else ''
        
        doc_link = f"https://docs.google.com/document/d/{document_id}/edit"
        return f"[BAŞARILI] Doküman okundu.\n🔗 Dokümanı aç: {doc_link}\n\nİçerik:\n{text}"
    except Exception as e:
        return f"[HATA] Doküman okunurken bir sorun meydana geldi: {e}"

def append_to_sheets(spreadsheet_id, range_name, values):
    """
    Belirtilen Google Sheets tablosuna (örn: 'Sayfa1!A:C') yeni satır verisi ekler.
    values formatı örnek: [['Değer1', 'Değer2']]
    """
    try:
        creds = authenticate_google()
        service = build('sheets', 'v4', credentials=creds)
        
        body = {
            'values': values
        }
        
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption='RAW', body=body).execute()
            
        sheet_link = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        updated = result.get('updates').get('updatedCells')
        return f"[BAŞARILI] {updated} hücre güncellendi (Eklendi).\n🔗 Tabloyu görüntüle: {sheet_link}"
    except Exception as e:
        return f"[HATA] Tabloya veri eklenirken bir sorun meydana geldi: {e}"

def create_blank_slide(presentation_title):
    """
    Belirtilen başlıkla yeni bir Google Sunular (Slides) dosyası oluşturur.
    """
    try:
        creds = authenticate_google()
        service = build('slides', 'v1', credentials=creds)
        
        body = {
            'title': presentation_title
        }
        
        presentation = service.presentations().create(body=body).execute()
        presentation_id = presentation.get('presentationId')
        link = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
        
        return f"[BAŞARILI] '{presentation_title}' adlı sunu oluşturuldu.\n🔗 Sunuyu aç: {link}"
    except Exception as e:
        return f"[HATA] Sunu oluşturulurken bir sorun meydana geldi: {e}"

def create_blank_document(title):
    """
    Belirtilen başlıkla yeni bir boş Google Dokümanı (Docs) oluşturur.
    """
    try:
        creds = authenticate_google()
        service = build('docs', 'v1', credentials=creds)
        
        body = {
            'title': title
        }
        
        document = service.documents().create(body=body).execute()
        document_id = document.get('documentId')
        link = f"https://docs.google.com/document/d/{document_id}/edit"
        
        return f"[BAŞARILI] '{title}' adlı doküman oluşturuldu.\n🔗 Dokümanı aç: {link}"
    except Exception as e:
        return f"[HATA] Doküman oluşturulurken bir sorun meydana geldi: {e}"


# =====================================================
# YENİ CRUD ARAÇLARI
# =====================================================

def read_emails(query="is:unread", max_results=5):
    """
    Gmail API kullanarak gelen kutusunu belirtilen sorguya göre tarar.
    Gönderen, konu ve kısa içerik (snippet) bilgilerini döndürür.
    Örnek sorgular: 'is:unread', 'from:ali@example.com', 'subject:Toplantı'
    """
    try:
        creds = authenticate_google()
        service = build('gmail', 'v1', credentials=creds)

        results = service.users().messages().list(
            userId='me', q=query, maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            return f"[BİLGİ] '{query}' sorgusuna uyan e-posta bulunamadı."

        output = f"[BAŞARILI] '{query}' sorgusuna uyan {len(messages)} e-posta bulundu:\n\n"
        for i, msg_meta in enumerate(messages, 1):
            msg = service.users().messages().get(
                userId='me', id=msg_meta['id'], format='metadata',
                metadataHeaders=['From', 'Subject']
            ).execute()

            headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
            sender = headers.get('From', 'Bilinmeyen')
            subject = headers.get('Subject', '(Konu yok)')
            snippet = msg.get('snippet', '')
            mail_link = f"https://mail.google.com/mail/u/0/#inbox/{msg_meta['id']}"

            output += f"  {i}. [{subject}]({mail_link})\n     Gönderen: {sender}\n     Özet: {snippet}\n\n"

        return output
    except Exception as e:
        return f"[HATA] E-postalar okunurken bir sorun meydana geldi: {e}"


def send_email_directly(to, subject, body):
    """
    Gmail API kullanarak belirtilen adrese e-postayı doğrudan gönderir.
    Taslak oluşturmaz, anında iletir.
    """
    try:
        creds = authenticate_google()
        service = build('gmail', 'v1', credentials=creds)

        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['Subject'] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_body = {'raw': encoded_message}

        sent = service.users().messages().send(userId='me', body=send_body).execute()
        msg_id = sent.get('id', '')
        return f"[BAŞARILI] E-posta '{to}' adresine başarıyla gönderildi.\nMesaj ID: {msg_id}"
    except Exception as e:
        return f"[HATA] E-posta gönderilirken bir sorun meydana geldi: {e}"


def list_calendar_events(days=7):
    """
    Google Calendar API kullanarak bugünden itibaren belirtilen gün sayısı kadar
    ileriye dönük etkinlikleri (isim, tarih, ID) listeler.
    """
    try:
        creds = authenticate_google()
        service = build('calendar', 'v3', credentials=creds)

        now = datetime.datetime.now(datetime.timezone.utc)
        time_max = now + datetime.timedelta(days=days)

        events_result = service.events().list(
            calendarId='primary',
            timeMin=now.isoformat(),
            timeMax=time_max.isoformat(),
            maxResults=20,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            return f"[BİLGİ] Önümüzdeki {days} gün içinde takvimde etkinlik bulunamadı."

        output = f"[BAŞARILI] Önümüzdeki {days} gün içindeki etkinlikler:\n\n"
        for i, event in enumerate(events, 1):
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', '(Başlıksız)')
            event_link = event.get('htmlLink', 'https://calendar.google.com')
            output += f"  {i}. [{summary}]({event_link})\n     📅 Tarih: {start}\n\n"

        output += "\n---[DAHİLİ BİLGİ - KULLANICIYA GÖSTERME]---\n"
        for i, event in enumerate(events, 1):
            output += f"{i}={event.get('id', '')}\n"

        return output
    except Exception as e:
        return f"[HATA] Takvim etkinlikleri alınırken bir sorun meydana geldi: {e}"


def delete_calendar_event(event_id):
    """
    Google Calendar API kullanarak verilen event_id'ye sahip etkinliği
    kullanıcının birincil takviminden siler.
    """
    try:
        creds = authenticate_google()
        service = build('calendar', 'v3', credentials=creds)

        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return f"[BAŞARILI] '{event_id}' ID'li etkinlik takvimden silindi."
    except Exception as e:
        return f"[HATA] Etkinlik silinirken bir sorun meydana geldi: {e}"


def delete_drive_file(file_id):
    """
    Google Drive API kullanarak belirtilen dosyayı çöp kutusuna taşır (trash).
    Kalıcı silme yerine güvenli çöp kutusuna gönderir.
    """
    try:
        creds = authenticate_google()
        service = build('drive', 'v3', credentials=creds)

        service.files().update(
            fileId=file_id,
            body={'trashed': True}
        ).execute()
        return f"[BAŞARILI] '{file_id}' ID'li dosya çöp kutusuna taşındı."
    except Exception as e:
        return f"[HATA] Dosya silinirken bir sorun meydana geldi: {e}"


def move_drive_file(file_id, folder_id):
    """
    Google Drive API kullanarak belirtilen dosyayı hedef klasöre taşır.
    addParents/removeParents mantığını kullanır.
    """
    try:
        creds = authenticate_google()
        service = build('drive', 'v3', credentials=creds)

        # Mevcut parent klasörlerini al
        file_info = service.files().get(
            fileId=file_id, fields='parents'
        ).execute()
        previous_parents = ",".join(file_info.get('parents', []))

        # Dosyayı yeni klasöre taşı
        service.files().update(
            fileId=file_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()

        folder_link = f"https://drive.google.com/drive/folders/{folder_id}"
        return f"[BAŞARILI] Dosya '{folder_id}' klasörüne taşındı.\n🔗 Klasörü görüntüle: {folder_link}"
    except Exception as e:
        return f"[HATA] Dosya taşınırken bir sorun meydana geldi: {e}"


def write_to_google_doc(document_id, text):
    """
    Google Docs API kullanarak mevcut bir dokümanın sonuna metin ekler.
    documents().batchUpdate() ve insertText kullanır.
    """
    try:
        creds = authenticate_google()
        service = build('docs', 'v1', credentials=creds)

        # Dokümanın mevcut uzunluğunu al
        document = service.documents().get(documentId=document_id).execute()
        body_content = document.get('body', {}).get('content', [])

        # Son element'in endIndex'ini bul (doküman sonuna yazmak için)
        end_index = 1
        for element in body_content:
            if 'endIndex' in element:
                end_index = element['endIndex']

        # Dokümanın sonuna metin ekle (endIndex - 1 pozisyonuna)
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': end_index - 1,
                    },
                    'text': text
                }
            }
        ]

        service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()

        doc_link = f"https://docs.google.com/document/d/{document_id}/edit"
        return f"[BAŞARILI] Metin dokümana eklendi.\n🔗 Dokümanı aç: {doc_link}"
    except Exception as e:
        return f"[HATA] Dokümana yazılırken bir sorun meydana geldi: {e}"


def read_google_sheet(spreadsheet_id, range_name):
    """
    Google Sheets API kullanarak belirtilen aralıktaki tablo verisini okur
    ve string olarak döndürür.
    Örnek range_name: 'Sayfa1!A1:C10'
    """
    try:
        creds = authenticate_google()
        service = build('sheets', 'v4', credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])

        if not values:
            return f"[BİLGİ] '{range_name}' aralığında veri bulunamadı."

        sheet_link = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        output = f"[BAŞARILI] '{range_name}' aralığındaki veriler:\n\n"
        for i, row in enumerate(values):
            output += f"  Satır {i+1}: {' | '.join(str(cell) for cell in row)}\n"

        output += f"\n🔗 Tabloyu görüntüle: {sheet_link}"
        return output
    except Exception as e:
        return f"[HATA] Tablo verisi okunurken bir sorun meydana geldi: {e}"


def add_slide_to_presentation(presentation_id, title_text):
    """
    Google Slides API kullanarak mevcut sunuma yeni bir slayt sayfası ekler
    ve başlık yazar. presentations().batchUpdate() kullanır.
    """
    try:
        creds = authenticate_google()
        service = build('slides', 'v1', credentials=creds)

        import uuid
        slide_id = f"slide_{uuid.uuid4().hex[:8]}"
        title_id = f"title_{uuid.uuid4().hex[:8]}"

        requests = [
            {
                'createSlide': {
                    'objectId': slide_id,
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE_ONLY'
                    },
                    'placeholderIdMappings': [
                        {
                            'layoutPlaceholder': {
                                'type': 'TITLE',
                                'index': 0
                            },
                            'objectId': title_id
                        }
                    ]
                }
            },
            {
                'insertText': {
                    'objectId': title_id,
                    'text': title_text,
                    'insertionIndex': 0
                }
            }
        ]

        service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': requests}
        ).execute()

        slide_link = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
        return f"[BAŞARILI] Sunuma '{title_text}' başlıklı yeni slayt eklendi.\n🔗 Sunuyu aç: {slide_link}"
    except Exception as e:
        return f"[HATA] Sunuma slayt eklenirken bir sorun meydana geldi: {e}"


if __name__ == '__main__':
    print("=== Google Workspace Araçları Test (tools.py) ===\n")
    
    # 1. Google Drive Testi
    print(">> Drive API: Son 3 Dosya Listeleniyor...")
    print(list_recent_drive_files(limit=3))
    print("-" * 50)
    
    # 2. Gmail Taslak E-posta Testi
    print(">> Gmail API: Taslak E-posta Oluşturuluyor...")
    print(create_draft_email(
        to_email="ornek.alici@example.com",
        subject="Otonom Asistan - Test E-postası",
        body_text="Merhaba,\nBu e-posta taslağı Otonom Asistan tarafından otomatik olarak oluşturulmuştur."
    ))
    print("-" * 50)
    
    # 3. Google Calendar Testi
    print(">> Calendar API: Test Etkinliği Oluşturuluyor...")
    # Şu anki saate 1 saat ekleyerek örnek bir etkinlik için başlangıç ve bitiş tanımlayalım
    now = datetime.datetime.now().astimezone() # Yerel saat dilimi ile
    start = now + datetime.timedelta(hours=1)
    end = start + datetime.timedelta(hours=1)
    
    start_iso = start.isoformat()
    end_iso = end.isoformat()
    
    print(Calendar(
        summary="Otonom Asistan Test Toplantısı",
        start_time=start_iso,
        end_time=end_iso
    ))
    print("-" * 50)
    print("\nTest işlemleri tamamlandı.")
