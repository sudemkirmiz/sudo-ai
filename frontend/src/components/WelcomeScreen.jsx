import { Mail, CalendarDays, HardDrive, Globe } from 'lucide-react';

const CARDS = [
    {
        icon: Mail,
        title: 'E-posta Yönetimi',
        desc: 'Gmail okuma, taslak oluşturma ve doğrudan gönderme',
        gradient: 'linear-gradient(135deg, #fce7f3, #f5d0fe)',
        iconGradient: 'linear-gradient(135deg, #f472b6, #c084fc)',
    },
    {
        icon: CalendarDays,
        title: 'Takvim Yönetimi',
        desc: 'Etkinlik oluşturma, listeleme ve silme',
        gradient: 'linear-gradient(135deg, #f3e8ff, #e9d5ff)',
        iconGradient: 'linear-gradient(135deg, #a78bfa, #818cf8)',
    },
    {
        icon: HardDrive,
        title: 'Google Drive Erişim',
        desc: 'Dosya listeleme, indirme, silme ve taşıma',
        gradient: 'linear-gradient(135deg, #ede9fe, #ddd6fe)',
        iconGradient: 'linear-gradient(135deg, #c084fc, #f472b6)',
    },
    {
        icon: Globe,
        title: 'Doküman & Tablo',
        desc: 'Docs okuma/yazma, Sheets veri ekleme/okuma',
        gradient: 'linear-gradient(135deg, #e0e7ff, #c7d2fe)',
        iconGradient: 'linear-gradient(135deg, #818cf8, #a78bfa)',
    },
];

export default function WelcomeScreen({ username }) {
    return (
        <div className="flex-1 flex flex-col items-center justify-center px-8 pb-4">
            {/* Greeting */}
            <div className="text-center mb-12 max-w-xl">
                <h1
                    className="text-5xl md:text-6xl font-extrabold mb-4 bg-clip-text text-transparent leading-tight"
                    style={{ backgroundImage: 'linear-gradient(135deg, #9333ea, #f472b6, #c084fc)' }}
                >
                    Merhaba {username}
                </h1>
                <p className="text-xl md:text-2xl font-light" style={{ color: 'var(--text-secondary)' }}>
                    Bugün nasıl yardımcı olabilirim?
                </p>
                <p className="text-xs mt-3 tracking-[0.2em] uppercase font-semibold" style={{ color: 'var(--accent-light)' }}>
                    Sudo AI · Your Workspace, Root Permissions
                </p>
            </div>

            {/* Info Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 max-w-4xl w-full">
                {CARDS.map((card, i) => (
                    <div
                        key={i}
                        className="group rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1.5 hover:shadow-xl cursor-default"
                        style={{
                            background: card.gradient,
                            border: '1px solid var(--border-color)',
                        }}
                    >
                        <div
                            className="w-12 h-12 rounded-2xl flex items-center justify-center mb-4 transition-transform duration-300 group-hover:scale-110 shadow-md"
                            style={{ background: card.iconGradient }}
                        >
                            <card.icon size={24} className="text-white" />
                        </div>
                        <h3 className="text-sm font-bold mb-1.5" style={{ color: 'var(--text-primary)' }}>
                            {card.title}
                        </h3>
                        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                            {card.desc}
                        </p>
                    </div>
                ))}
            </div>
        </div>
    );
}
