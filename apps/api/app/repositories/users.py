import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import User, UserRole, UserStatus


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_firebase_uid(self, firebase_uid: str) -> User | None:
        result = await self.session.execute(select(User).where(User.firebase_uid == firebase_uid))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_users(
        self,
        *,
        search: str | None = None,
        role: UserRole | None = None,
        status: UserStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[User], int]:
        filters = []
        if search:
            search_pattern = f"%{search.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(User.email).like(search_pattern),
                    func.lower(User.full_name).like(search_pattern),
                )
            )
        if role is not None:
            filters.append(User.role == role)
        if status is not None:
            filters.append(User.status == status)

        count_stmt = select(func.count(User.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = select(User)
        if filters:
            stmt = stmt.where(*filters)
        stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars()), total_count

    def create_candidate(
        self,
        *,
        firebase_uid: str,
        email: str,
        full_name: str,
        email_verified: bool,
        auth_provider: str | None,
        role: UserRole = UserRole.CANDIDATE,
    ) -> User:
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            full_name=full_name,
            role=role,
            status=UserStatus.ACTIVE,
            email_verified=email_verified,
            auth_provider=auth_provider,
            last_login_at=datetime.now(UTC),
        )
        self.session.add(user)
        return user

    def update_status(self, user: User, status: UserStatus) -> None:
        user.status = status

    def update_login_metadata(
        self,
        user: User,
        *,
        email_verified: bool,
        auth_provider: str | None,
    ) -> None:
        user.email_verified = email_verified
        user.auth_provider = auth_provider
        user.last_login_at = datetime.now(UTC)

    async def commit_and_refresh(self, user: User) -> User:
        await self.session.commit()
        await self.session.refresh(user)
        return user
