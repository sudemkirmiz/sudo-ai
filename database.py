"""
Sudo AI — Veritabanı Katmanı
SQLAlchemy ORM ile SQLite veritabanı yönetimi.
Conversations ve Messages tablolarını içerir.
"""

import uuid
from datetime import datetime

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# --- Veritabanı Yapılandırması ---
DATABASE_URL = "sqlite:///./sudo_ai.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite için gerekli (FastAPI async uyumluluğu)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# =====================================================
# ORM Modelleri
# =====================================================

class Conversation(Base):
    """Sohbet oturumlarını temsil eder."""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, default="Yeni Sohbet")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Bir sohbetin birden fazla mesajı olabilir
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat()
        }


class Message(Base):
    """Sohbet mesajlarını temsil eder."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)       # "user", "assistant", "system", "tool"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat()
        }


# Tabloları oluştur (yoksa)
Base.metadata.create_all(bind=engine)


# =====================================================
# FastAPI Dependency — Session Yönetimi
# =====================================================

def get_db():
    """
    Her request için yeni bir DB session oluşturur,
    request bittiğinde kapatır. FastAPI Depends() ile kullanılır.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================
# Yardımcı Fonksiyonlar (CRUD)
# =====================================================

def create_conversation(db, title: str = "Yeni Sohbet") -> Conversation:
    """Yeni bir sohbet oturumu oluşturur ve veritabanına kaydeder."""
    conv = Conversation(title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def list_conversations(db) -> list:
    """Tüm sohbetleri oluşturulma tarihine göre (en yeni en üstte) döndürür."""
    return db.query(Conversation).order_by(Conversation.created_at.desc()).all()


def get_messages(db, conversation_id: str) -> list:
    """Belirli bir sohbetin tüm mesajlarını kronolojik sırayla döndürür."""
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )


def add_message(db, conversation_id: str, role: str, content: str) -> Message:
    """Belirtilen sohbete yeni bir mesaj ekler."""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_conversation(db, conversation_id: str):
    """Tek bir sohbeti ID'ye göre getirir."""
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def update_conversation_title(db, conversation_id: str, title: str):
    """Sohbet başlığını günceller."""
    conv = get_conversation(db, conversation_id)
    if conv:
        conv.title = title
        db.commit()
        db.refresh(conv)
    return conv


def delete_conversation(db, conversation_id: str) -> bool:
    """Belirtilen sohbeti ve tüm mesajlarını siler."""
    conv = get_conversation(db, conversation_id)
    if conv:
        db.delete(conv)  # cascade="all, delete-orphan" sayesinde mesajlar da silinir
        db.commit()
        return True
    return False

