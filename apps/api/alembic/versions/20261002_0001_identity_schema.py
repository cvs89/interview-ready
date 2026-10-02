"""Create foundational identity and interviewer schema.

Revision ID: 20261002_0001
Revises:
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261002_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = postgresql.ENUM(
    "CANDIDATE", "INTERVIEWER", "ADMIN", name="user_role", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("firebase_uid", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column(
            "role",
            user_role,
            server_default=sa.text("'CANDIDATE'::user_role"),
            nullable=False,
        ),
        sa.Column("email_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("auth_provider", sa.String(length=100), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("email = lower(email)", name="ck_users_email_normalized"),
        sa.CheckConstraint("length(trim(full_name)) > 0", name="ck_users_full_name_nonempty"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("firebase_uid", name="uq_users_firebase_uid"),
    )
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "interviewer_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("years_experience", sa.Integer(), nullable=True),
        sa.Column("default_rate_minor", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.CHAR(length=3), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "years_experience IS NULL OR years_experience >= 0",
            name="ck_interviewer_profiles_years_nonnegative",
        ),
        sa.CheckConstraint(
            "default_rate_minor IS NULL OR default_rate_minor >= 0",
            name="ck_interviewer_profiles_rate_nonnegative",
        ),
        sa.CheckConstraint(
            "currency IS NULL OR currency = upper(currency)",
            name="ck_interviewer_profiles_currency_uppercase",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_interviewer_profiles_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_interviewer_profiles"),
        sa.UniqueConstraint("user_id", name="uq_interviewer_profiles_user_id"),
    )

    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_skills_name_nonempty"),
        sa.CheckConstraint("length(trim(slug)) > 0", name="ck_skills_slug_nonempty"),
        sa.PrimaryKeyConstraint("id", name="pk_skills"),
        sa.UniqueConstraint("name", name="uq_skills_name"),
        sa.UniqueConstraint("slug", name="uq_skills_slug"),
    )

    op.create_table(
        "interviewer_skills",
        sa.Column("interviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("years_experience", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "years_experience IS NULL OR years_experience >= 0",
            name="ck_interviewer_skills_years_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["interviewer_id"],
            ["interviewer_profiles.id"],
            name="fk_interviewer_skills_interviewer_id_interviewer_profiles",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name="fk_interviewer_skills_skill_id_skills",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("interviewer_id", "skill_id", name="pk_interviewer_skills"),
        sa.UniqueConstraint("interviewer_id", "skill_id", name="uq_interviewer_skills_pair"),
    )
    op.create_index("ix_interviewer_skills_skill_id", "interviewer_skills", ["skill_id"])


def downgrade() -> None:
    op.drop_index("ix_interviewer_skills_skill_id", table_name="interviewer_skills")
    op.drop_table("interviewer_skills")
    op.drop_table("skills")
    op.drop_table("interviewer_profiles")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_table("users")
    user_role.drop(op.get_bind(), checkfirst=True)
