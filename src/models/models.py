from sqlalchemy.dialects.postgresql import TEXT, JSONB, INTEGER, BOOLEAN
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from .base_model import BaseModel


class Users(BaseModel):
    __tablename__ = "users"
    id = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    uid = mapped_column(TEXT, unique=True, nullable=False)
    tid = mapped_column(TEXT, nullable=True)


class Assistants(BaseModel):
    __tablename__ = "assistants"
    id = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    aid = mapped_column(TEXT, unique=True, nullable=True)
    name = mapped_column(TEXT, unique=True, nullable=False)
    prompt = mapped_column(TEXT, nullable=True)


class Tools(BaseModel):
    __tablename__ = "tools"
    id = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    name = mapped_column(TEXT, unique=True, nullable=False)
    src = mapped_column(JSONB)
    sync = mapped_column(BOOLEAN, default=True)


class Assistants_Tools(BaseModel):
    __tablename__ = 'assistants_tools'
    id = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    assistant_id = mapped_column(INTEGER, ForeignKey('assistants.id'), nullable=False)
    tool_id = mapped_column(INTEGER, ForeignKey('tools.id'), nullable=False)


class Values(BaseModel):
    __tablename__ = 'values'
    id = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    name = mapped_column(TEXT, unique=True, nullable=False)


class Users_Values(BaseModel):
    __tablename__ = 'users_values'
    id = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    user_id = mapped_column(INTEGER, ForeignKey('users.id'), nullable=False)
    value_id = mapped_column(INTEGER, ForeignKey('values.id'), nullable=False)
    proof_count = mapped_column(INTEGER, default=0, nullable=False)


class Proofs(BaseModel):
    __tablename__ = 'proofs'
    id = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    content = mapped_column(TEXT, nullable=False)


class Users_Values_Proofs(BaseModel):
    __tablename__ = 'users_values_proofs'
    id = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    user_value_id = mapped_column(INTEGER, ForeignKey('users_values.id'), nullable=False)
    proof_id = mapped_column(INTEGER, ForeignKey('proofs.id'), nullable=False)
    
    
class Vector_Stores(BaseModel):
    __tablename__ = 'vector_stores'
    id = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    vsid = mapped_column(TEXT)
    name = mapped_column(TEXT, nullable=False)


class Files(BaseModel):
    __tablename__ = 'files'
    id = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    fid = mapped_column(TEXT)
    name = mapped_column(TEXT, nullable=False)


class Vector_Stores_Files(BaseModel):
    __tablename__ = 'vector_stores_files'
    id = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    vector_store_id = mapped_column(INTEGER, ForeignKey('vector_stores.id'), nullable=False)
    file_id = mapped_column(INTEGER, ForeignKey('files.id'), nullable=False)
    