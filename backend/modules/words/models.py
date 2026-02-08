from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship

from backend.core.database import Base


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True)
    english = Column(String, nullable=False, unique=True, index=True)
    transcription = Column(String)
    part_of_speech = Column(String)
    translations = Column(JSON)
    frequency_rank = Column(Integer)
    cefr_level = Column(String)

    contexts = relationship(
        "WordContext", back_populates="word", cascade="all,delete"
    )

    def __repr__(self) -> str:
        return f"<Word id={self.id} english='{self.english}'>"


class WordContext(Base):
    __tablename__ = "word_contexts"

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    sentence_en = Column(String, nullable=False)
    sentence_ru = Column(String)
    source = Column(String)
    difficulty = Column(Integer, default=1)

    word = relationship("Word", back_populates="contexts")

    def __repr__(self) -> str:
        return f"<WordContext id={self.id} word_id={self.word_id}>"
