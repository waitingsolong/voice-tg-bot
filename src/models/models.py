from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base_model import BaseModel, Base
    
    
class Users(BaseModel):
    __tablename__ = "users"
    uid: Mapped[Text] = mapped_column(Text, primary_key=True)
    tid: Mapped[Text] = mapped_column(Text, nullable=True)
    values: Mapped[Text] = mapped_column(Text, nullable=True)


class Assistants(BaseModel):
    __tablename__ = "assistants"
    aid: Mapped[Text] = mapped_column(Text, nullable=True)
    name: Mapped[Text] = mapped_column(Text, primary_key=True)
    prompt: Mapped[Text] = mapped_column(Text, nullable=True)