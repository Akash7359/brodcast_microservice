from sqlalchemy import (
    Column, Integer, String, Text, DateTime, JSON, ForeignKey, func
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    mappings = relationship("ProductCategoryTemplateMapping", back_populates="project")


class CategoryType(Base):
    __tablename__ = "category_type"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    mappings = relationship("ProductCategoryTemplateMapping", back_populates="category")


class ProductCategoryTemplateMapping(Base):
    __tablename__ = "product_category_template_mapping"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    category_type_id = Column(Integer, ForeignKey("category_type.id"), nullable=False)
    broadcast_channel_type = Column(Integer, nullable=False)  # 1=Email, 2=SMS, 3=Both
    template_path = Column(String(300), nullable=False)
    subject = Column(String(300), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="mappings")
    category = relationship("CategoryType", back_populates="mappings")


class SMTPDetail(Base):
    __tablename__ = "smtp_details"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    category_type_id = Column(Integer, ForeignKey("category_type.id"), nullable=True)
    broadcast_channel_type = Column(Integer, nullable=False)
    recipient_email = Column(String(255), nullable=True)
    recipient_mobile = Column(String(20), nullable=True)
    request_payload = Column(JSON, nullable=True)
    response_payload = Column(JSON, nullable=True)
    status = Column(Integer, default=1)  # 1=pending, 2=sent, 3=failed
    request_ip = Column(String(50), nullable=True)
    request_path = Column(String(300), nullable=True)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
