import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gerekli API kapsamları
SCOPES = [
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
]

def authenticate_google():
    """
    Google Workspace API'leri için kimlik doğrulama işlemini yönetir.
    Mevcut token.json'ı kontrol eder, geçerli değilse veya yoksa credentials.json
    kullanarak yeni token alır ve kaydeder.
    """
    creds = None
    
    # Daha önce alınmış ve geçerli olan bir token.json var mı kontrol et
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            print(f"Mevcut token.json dosyası okunurken hata oluştu: {e}")

    # Geçerli bir kimlik bilgisi (credentials) yoksa yenile veya baştan giriş yap
    if not creds or not creds.valid:
        try:
            # Token var ama süresi dolmuşsa yenilemeyi dene
            if creds and creds.expired and creds.refresh_token:
                print("Mevcut token'ın süresi dolmuş, yenileniyor...")
                creds.refresh(Request())
            else:
                # Token yoksa veya yenilenemiyorsa flow başlat (Yerel web sunucusu üzerinden)
                print("Yeni kimlik doğrulama süreci başlatılıyor...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Başarılı işlemin ardından yeni (veya yenilenmiş) token'ı dosyaya yedekle
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
                print("Kimlik doğrulaması tamamlandı. Yeni token.json dosyası başarıyla kaydedildi.")
                
        except Exception as e:
            print(f"Kimlik doğrulama (OAuth) akışında bir hata meydana geldi: {e}")
            raise  # Hatayı dışarı ileterek çağıran yerin haberdar olmasını sağla
            
    return creds

if __name__ == '__main__':
    print("Google OAuth 2.0 Kimlik Doğrulama Testi Başlıyor...")
    try:
        credentials = authenticate_google()
        if credentials and credentials.valid:
            print("\n[BAŞARILI] Token alındı ve test başarıyla tamamlandı.")
        else:
            print("\n[HATA] Geçerli bir token elde edilemedi.")
    except Exception as e:
        print(f"\n[KRİTİK HATA] Test aşamasında beklenmedik bir sorun oluştu: {e}")
