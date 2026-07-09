"""Sprint 8: Add model_versions, knowledge_documents, conversations,
conversation_messages tables; extend audit_logs with rich fields.

Revision ID: c8f4d2a1e973
Revises: b7c3e1d4f892
Create Date: 2026-07-08 17:30:00.000000

Sprint 8: AI Manufacturing Intelligence
Additive migration only.  No existing columns are modified.
New tables: model_versions, knowledge_documents, conversations,
            conversation_messages
Extended table: audit_logs (3 new nullable columns)
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8f4d2a1e973"
down_revision: Union[str, None] = "b7c3e1d4f892"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── model_versions ────────────────────────────────────────────────────────
    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("version_name", sa.String(200), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column(
            "deployment_status", sa.String(20), nullable=False, server_default="staging"
        ),
        sa.Column("map_score", sa.Float(), nullable=True),
        sa.Column("precision", sa.Float(), nullable=True),
        sa.Column("recall", sa.Float(), nullable=True),
        sa.Column("training_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dataset_name", sa.String(200), nullable=True),
        sa.Column("trained_by", sa.String(100), nullable=True),
        sa.Column("framework", sa.String(100), nullable=True),
        sa.Column("commit_hash", sa.String(64), nullable=True),
        sa.Column("artifact_path", sa.String(512), nullable=True),
        sa.Column("model_size_mb", sa.Float(), nullable=True),
        sa.Column("parameter_count", sa.Integer(), nullable=True),
        sa.Column("parent_version", sa.String(200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # SoftDeleteMixin + TimestampMixin
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version_name", name="uq_model_versions_version_name"),
    )
    op.create_index("ix_model_versions_id", "model_versions", ["id"], unique=False)
    op.create_index(
        "ix_model_versions_version_name",
        "model_versions",
        ["version_name"],
        unique=True,
    )
    op.create_index(
        "ix_model_versions_deployment_status",
        "model_versions",
        ["deployment_status"],
        unique=False,
    )
    op.create_index(
        "ix_model_versions_is_deleted", "model_versions", ["is_deleted"], unique=False
    )
    op.create_index(
        "ix_model_versions_created_at", "model_versions", ["created_at"], unique=False
    )

    # ── knowledge_documents ───────────────────────────────────────────────────
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("doc_type", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("tags", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_documents_id", "knowledge_documents", ["id"], unique=False
    )
    op.create_index(
        "ix_knowledge_documents_title", "knowledge_documents", ["title"], unique=False
    )
    op.create_index(
        "ix_knowledge_documents_doc_type",
        "knowledge_documents",
        ["doc_type"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_documents_is_active",
        "knowledge_documents",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_documents_is_deleted",
        "knowledge_documents",
        ["is_deleted"],
        unique=False,
    )

    # ── conversations ─────────────────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("session_key", sa.String(200), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("context_summary", sa.Text(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_conversations_user"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_key", name="uq_conversations_session_key"),
    )
    op.create_index("ix_conversations_id", "conversations", ["id"], unique=False)
    op.create_index(
        "ix_conversations_session_key", "conversations", ["session_key"], unique=True
    )
    op.create_index(
        "ix_conversations_user_id", "conversations", ["user_id"], unique=False
    )
    op.create_index(
        "ix_conversations_is_deleted", "conversations", ["is_deleted"], unique=False
    )

    # ── conversation_messages ─────────────────────────────────────────────────
    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("conversation_id", sa.String(36), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        # TimestampMixin (no SoftDelete — messages are immutable)
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name="fk_conversation_messages_conversation",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_messages_id", "conversation_messages", ["id"], unique=False
    )
    op.create_index(
        "ix_conversation_messages_conversation_id",
        "conversation_messages",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_messages_timestamp",
        "conversation_messages",
        ["timestamp"],
        unique=False,
    )

    # ── audit_logs — additive new columns ─────────────────────────────────────
    op.add_column("audit_logs", sa.Column("old_value", sa.Text(), nullable=True))
    op.add_column("audit_logs", sa.Column("new_value", sa.Text(), nullable=True))
    op.add_column("audit_logs", sa.Column("request_id", sa.String(64), nullable=True))
    op.create_index(
        "ix_audit_logs_request_id", "audit_logs", ["request_id"], unique=False
    )


def downgrade() -> None:
    # Remove audit_logs new columns
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_column("audit_logs", "request_id")
    op.drop_column("audit_logs", "new_value")
    op.drop_column("audit_logs", "old_value")

    # Drop conversation_messages
    op.drop_index(
        "ix_conversation_messages_timestamp", table_name="conversation_messages"
    )
    op.drop_index(
        "ix_conversation_messages_conversation_id", table_name="conversation_messages"
    )
    op.drop_index("ix_conversation_messages_id", table_name="conversation_messages")
    op.drop_table("conversation_messages")

    # Drop conversations
    op.drop_index("ix_conversations_is_deleted", table_name="conversations")
    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_index("ix_conversations_session_key", table_name="conversations")
    op.drop_index("ix_conversations_id", table_name="conversations")
    op.drop_table("conversations")

    # Drop knowledge_documents
    op.drop_index("ix_knowledge_documents_is_deleted", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_is_active", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_doc_type", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_title", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_id", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")

    # Drop model_versions
    op.drop_index("ix_model_versions_created_at", table_name="model_versions")
    op.drop_index("ix_model_versions_is_deleted", table_name="model_versions")
    op.drop_index("ix_model_versions_deployment_status", table_name="model_versions")
    op.drop_index("ix_model_versions_version_name", table_name="model_versions")
    op.drop_index("ix_model_versions_id", table_name="model_versions")
    op.drop_table("model_versions")
