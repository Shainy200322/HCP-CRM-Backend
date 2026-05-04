from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float
from sqlalchemy.sql import func
from database.db import Base

class HCP(Base):
    __tablename__ = "hcps"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    specialty = Column(String(255))
    institution = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    territory = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String(255), nullable=False)
    interaction_type = Column(String(100), default="Meeting")
    date = Column(String(50))
    time = Column(String(20))
    attendees = Column(Text)
    topics_discussed = Column(Text)
    materials_shared = Column(JSON, default=[])
    samples_distributed = Column(JSON, default=[])
    sentiment = Column(String(50), default="Neutral")
    outcomes = Column(Text)
    follow_up_actions = Column(Text)
    ai_summary = Column(Text)
    ai_suggested_follow_ups = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100))
    role = Column(String(20))
    content = Column(Text)
    interaction_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())