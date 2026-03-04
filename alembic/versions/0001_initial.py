"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "category_type",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "product_category_template_mapping",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("category_type_id", sa.Integer(), sa.ForeignKey("category_type.id"), nullable=False),
        sa.Column("broadcast_channel_type", sa.Integer(), nullable=False),
        sa.Column("template_path", sa.String(300), nullable=False),
        sa.Column("subject", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "smtp_details",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("category_type_id", sa.Integer(), nullable=True),
        sa.Column("broadcast_channel_type", sa.Integer(), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=True),
        sa.Column("recipient_mobile", sa.String(20), nullable=True),
        sa.Column("request_payload", sa.JSON(), nullable=True),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("status", sa.Integer(), default=1),
        sa.Column("request_ip", sa.String(50), nullable=True),
        sa.Column("request_path", sa.String(300), nullable=True),
        sa.Column("created_date", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )


def downgrade():
    op.drop_table("smtp_details")
    op.drop_table("product_category_template_mapping")
    op.drop_table("category_type")
    op.drop_table("projects")
