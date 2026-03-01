# Sudo AI — Premium Google Workspace Agent

<div align="center">
  <img src="frontend/public/screenshot.png" alt="Sudo AI Premium Dashboard" width="800"/>
</div>

![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite%20%2B%20Tailwind-61DAFB?logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)
![LLM](https://img.shields.io/badge/AI-Gemini%20%7C%20Ollama-8A2BE2)

**Sudo AI**, günlük Google Workspace işlerinizi (Gmail, Takvim, Drive, Docs, Sheets, Slides) doğal dille otomatize etmenizi sağlayan yüksek yetenekli, *ReAct (Reasoning and Acting)* mantığıyla çalışan premium bir yapay zeka asistanıdır.

Eski Streamlit altyapısından, çok daha hızlı ve pürüzsüz bir kullanıcı deneyimi sunan **Client-Server (React + FastAPI)** mimarisine geçirilmiştir.

## ✨ Öne Çıkan "SaaS" Özellikleri

- 🎨 **Premium Modern Arayüz:** Apple/SaaS standartlarında pastel renk paleti, gelişmiş animasyonlar, pürüzsüz geçişler ve şık kavislerle tasarlanmış React tabanlı arayüz.
- ⚙️ **Dinamik Model Seçimi:** Arayüz üzerinden Google Gemini (Bulut) veya Ollama (Yerel) modelleri (Llama 3 vb.) arasında anında geçiş yapabilme.
- 🎙️ **Text-to-Speech (TTS):** Asistan mesajları için doğal Türkçe kadın sesi ile seslendirme özelliği. (URL ve Markdown bağlamları temizlenerek okunur).
- 📎 **RAG (Retrieval-Augmented Generation):** Chat üzerinden PDF veya TXT dosyası yükleyebilme, sürükle-bırak desteği ve belge içeriğine dayalı spesifik sohbet edebilme becerisi.
- 📆 **Akıllı Organizatör Butonları:** "Docs'a Aktar" ve "Takvime İşle" gibi tek tıkla mesaj içeriklerini sistem araçlarına (`Tool Calling`) aktaran aksiyon tuşları.
- ⏱️ **Canlı Geri Bildirim:** Kod blokları için "Kopyalandı!" panosu, "Düşünüyor..." zıplayan üç nokta animasyonu, Asistan adım adım araç çalıştırırken beliren *Pill Badge* geri bildirimleri.
- 🗄️ **Veritabanı Entegrasyonu:** SQLite tabanlı, sonsuz log tutabilen ve istediğinizde tek tıkla silinebilen sohbet geçmişi sistemi.

---

## ☁️ Google Workspace Yetenekleri (Araçlar)

Sudo AI sadece metin üretmez, sizin adınıza *gerçek işler* yapar:

- **Gmail:** İstediğiniz kişi ve içerikle taslak e-postalar hazırlar.
- **Takvim:** Gündeminizi okur, yeni etkinlik veya toplantılar planlar.
- **Drive:** Son dosyalarınızı listeler veya istediğiniz belgenin indirme linkini getirir.
- **Docs:** Kayıtlı Google Docs belgelerinizi doğrudan okur ve içeriğini yorumlar. Veya yeni doküman yaratarak kaydeder.
- **Sheets:** E-Tabloların (Excel) sonuna anında yeni satırlar/veriler ekler.
- **Slides:** Sıfırdan boş bir sunum dosyası oluşturur.

---

## 🛠️ Kurulum Rehberi

Projeyi yerel ortamınızda ayağa kaldırmak için aşağıdaki adımları sırayla (Backend ve Frontend olarak) izleyin.

### 1. Kimlik ve API Ayarları
Uygulama dizininin en üstünde (root) bir `.env` dosyası oluşturun ve Gemini anahtarınızı ekleyin:
```env
GEMINI_API_KEY=sizin_gemini_api_anahtariniz
```
*Not:* Google servisleriyle iletişim için **Google Cloud API** üzerinden Desktop App kimliği oluşturarak indirdiğiniz JSON dosyasını `credentials.json` adıyla root dizinine koymayı unutmayın.

### 2. Backend (FastAPI) Kurulumu

Python sanal ortamı kurarak gerekli bağımlılıkları indirin:
```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate # macOS / Linux

pip install -r requirements.txt
```

Arka yüz sunucusunu başlatın:
```bash
python -m uvicorn main:app --reload --port 8000
```
> Sunucu başarıyla çalıştığında API dokümantasyonuna [http://localhost:8000/docs](http://localhost:8000/docs) adresinden erişülebilir. Sistem otomatik olarak SQLite veritabanını (`database.db`) yaratacaktır.

### 3. Frontend (React) Kurulumu

Yeni bir terminal açın ve `/frontend` dizinine girin:
```bash
cd frontend
npm install
```

Sunucuyu ve React arayüzünü geliştirme modunda başlatın:
```bash
npm run dev
```
> Uygulama genellikle [http://localhost:5173/](http://localhost:5173/) üzerinde yayına girer. Tarayıcınızdan bu adresi açarak kullanmaya başlayabilirsiniz.

---

## 📂 Proje Mimarisi (Directory Structure)

```text
sudo-ai/
├── ⚙️ Backend (FastAPI)
│   ├── main.py              # API Endpoint'leri, SSE streaming ve ana asistan döngüsü
│   ├── database.py          # SQLAlchemy şemaları, SQLite entegrasyonu (CRUD)
│   ├── tools.py             # ReAct promptu ve Google Workspace fonksiyonları (Tool Calling)
│   ├── auth.py              # Google OAuth 2.0 ve Token yenileme işlemleri
│   ├── requirements.txt     # Python paket bağımlılıkları
│   └── .env                 # API anahtarları (Gizli)
│
├── 🎨 Frontend (React + Vite)
│   ├── index.html           # React root dosyası
│   ├── package.json         # Node bağımlılıkları (Tailwind, Lucide vb.)
│   ├── vite.config.js       # Vite yapılandırma ayarları
│   └── src/
│       ├── App.jsx          # Uygulama iskeleti, state yönetimi (React)
│       ├── index.css        # Tailwind direktifleri, animasyonlar ve global değişkenler
│       ├── services/
│       │   └── api.js       # Backend API proxy ve HTTP fetch fonksiyonları
│       └── components/
│           ├── ChatArea.jsx # Mesajlaşma alanı, TTS kancası ve Markdown render bileşeni
│           ├── ChatInput.jsx# Mesaj kutusu, Sesli Asistan (STT) ve dosya yükleme (RAG)
│           ├── Sidebar.jsx  # Chat geçmişi listeleme ve ayarlar butonu
│           └── Welcome.jsx  # Dinamik Onboarding (İsim alma) ve karşılama ekranı
```
