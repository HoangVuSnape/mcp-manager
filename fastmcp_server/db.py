from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, JSON, Boolean, select


class Base(DeclarativeBase):
    pass


class Spec(Base):
    __tablename__ = "specs"
    prefix: Mapped[str] = mapped_column(String(100), primary_key=True)
    config: Mapped[dict] = mapped_column(JSON)


class ToolStatus(Base):
    """Store enable/disable state for individual tools."""

    __tablename__ = "tools"
    prefix: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


async def init_db(db_url: str) -> async_sessionmaker[AsyncSession]:
    """Initialise the database and return a sessionmaker."""
    engine = create_async_engine(db_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_specs(session: AsyncSession) -> list[dict]:
    result = await session.scalars(select(Spec))
    return [spec.config for spec in result]


async def add_spec(session: AsyncSession, spec_cfg: dict) -> None:
    prefix = spec_cfg.get("prefix")
    if not prefix:
        raise ValueError("spec config must include a prefix")
    await session.merge(Spec(prefix=prefix, config=spec_cfg))
    await session.commit()


async def set_tool_enabled(
    session: AsyncSession, prefix: str, name: str, enabled: bool
) -> None:
    """Insert or update a tool's enabled state."""
    await session.merge(ToolStatus(prefix=prefix, name=name, enabled=enabled))
    await session.commit()


async def get_tool_statuses(
    session: AsyncSession, prefix: str | None = None
) -> list[ToolStatus]:
    stmt = select(ToolStatus)
    if prefix:
        stmt = stmt.where(ToolStatus.prefix == prefix)
    result = await session.scalars(stmt)
    return list(result)
