"""Add interview rubrics and candidate reviews.

Revision ID: 20261002_0005
Revises: 20261002_0004
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261002_0005"
down_revision: str | None = "20261002_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

rubric_status = postgresql.ENUM(
    "DRAFT",
    "SUBMITTED",
    "LOCKED",
    name="rubric_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    rubric_status.create(bind, checkfirst=True)

    # 1. Table interview_rubrics
    op.create_table(
        "interview_rubrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("technical_score", sa.SmallInteger(), nullable=True),
        sa.Column("problem_solving_score", sa.SmallInteger(), nullable=True),
        sa.Column("communication_score", sa.SmallInteger(), nullable=True),
        sa.Column("detailed_feedback", sa.Text(), nullable=True),
        sa.Column("action_items", sa.Text(), nullable=True),
        sa.Column("private_interviewer_notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            rubric_status,
            server_default=sa.text("'DRAFT'::rubric_status"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "technical_score IS NULL OR (technical_score >= 1 AND technical_score <= 5)",
            name="ck_rubrics_technical_score_range",
        ),
        sa.CheckConstraint(
            "problem_solving_score IS NULL OR "
            "(problem_solving_score >= 1 AND problem_solving_score <= 5)",
            name="ck_rubrics_problem_solving_score_range",
        ),
        sa.CheckConstraint(
            "communication_score IS NULL OR "
            "(communication_score >= 1 AND communication_score <= 5)",
            name="ck_rubrics_communication_score_range",
        ),
        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["bookings.id"],
            name="fk_rubrics_booking",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["interviewer_id"],
            ["users.id"],
            name="fk_rubrics_interviewer",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_interview_rubrics"),
        sa.UniqueConstraint("booking_id", name="uq_interview_rubrics_booking_id"),
    )
    op.create_index(
        "ix_interview_rubrics_booking_id",
        "interview_rubrics",
        ["booking_id"],
    )
    op.create_index(
        "ix_interview_rubrics_interviewer_id",
        "interview_rubrics",
        ["interviewer_id"],
    )
    op.create_index(
        "ix_interview_rubrics_status",
        "interview_rubrics",
        ["status"],
    )

    # 2. Table interviewer_reviews
    op.create_table(
        "interviewer_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("review", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_reviews_rating_range",
        ),
        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["bookings.id"],
            name="fk_reviews_booking",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["users.id"],
            name="fk_reviews_candidate",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["interviewer_id"],
            ["users.id"],
            name="fk_reviews_interviewer",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_interviewer_reviews"),
        sa.UniqueConstraint("booking_id", name="uq_interviewer_reviews_booking_id"),
    )
    op.create_index(
        "ix_interviewer_reviews_interviewer_id",
        "interviewer_reviews",
        ["interviewer_id"],
    )
    op.create_index(
        "ix_interviewer_reviews_candidate_id",
        "interviewer_reviews",
        ["candidate_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_interviewer_reviews_candidate_id", table_name="interviewer_reviews")
    op.drop_index("ix_interviewer_reviews_interviewer_id", table_name="interviewer_reviews")
    op.drop_table("interviewer_reviews")

    op.drop_index("ix_interview_rubrics_status", table_name="interview_rubrics")
    op.drop_index("ix_interview_rubrics_interviewer_id", table_name="interview_rubrics")
    op.drop_index("ix_interview_rubrics_booking_id", table_name="interview_rubrics")
    op.drop_table("interview_rubrics")

    rubric_status.drop(op.get_bind(), checkfirst=True)
