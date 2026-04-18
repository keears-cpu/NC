from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .config import AppSettings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_cached_database_url: str | None = None
_schema_initialized = False

CORE_STORAGE_TABLES = ("charts", "reports", "counselors")
PHASE1_FOUNDATION_TABLES = (
    "storage_audit_runs",
    "organizations",
    "organization_memberships",
    "report_runs",
    "report_versions",
    "access_events",
)
AUDIT_TABLES = CORE_STORAGE_TABLES + PHASE1_FOUNDATION_TABLES


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    return database_url


def get_engine(settings: AppSettings | None = None) -> AsyncEngine | None:
    global _engine, _session_factory, _cached_database_url
    settings = settings or get_settings()
    database_url = (settings.database_url or "").strip()
    if not database_url:
        return None

    normalized_url = _normalize_database_url(database_url)
    if _engine is not None and _cached_database_url == normalized_url:
        return _engine

    _engine = create_async_engine(
        normalized_url,
        future=True,
        pool_pre_ping=True,
        connect_args={"statement_cache_size": 0},
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    _cached_database_url = normalized_url
    return _engine


def get_session_factory(settings: AppSettings | None = None) -> async_sessionmaker[AsyncSession] | None:
    engine = get_engine(settings=settings)
    if engine is None:
        return None
    return _session_factory


SCHEMA_STATEMENTS = [
    """
    create table if not exists counselors (
        id bigserial primary key,
        created_at timestamptz not null default now(),
        updated_at timestamptz not null default now(),
        name text,
        access_code text not null unique,
        start_date date,
        end_date date,
        status text not null default 'active',
        notes text
    )
    """,
    """
    create table if not exists charts (
        record_id text primary key,
        chart_id text not null unique,
        created_at timestamptz not null default now(),
        updated_at timestamptz not null default now(),
        engine_name text,
        status text,
        source_type text,
        extraction_mode text,
        classification text,
        notes text,
        person_name text,
        phone text,
        email text,
        counselor_code text,
        tester_local_id text,
        birth_date text not null,
        birth_time_local text,
        timezone text,
        birth_place_name text,
        country_code text,
        latitude double precision,
        longitude double precision,
        zodiac_type text,
        house_system text,
        node_mode text,
        lilith_mode text,
        fortune_formula text,
        core_complete boolean,
        soft_missing_json jsonb,
        warnings_json jsonb,
        chart_json jsonb,
        chart_svg text,
        chart_svg_updated_at timestamptz,
        report_preset text,
        report_addons_json jsonb,
        report_id text,
        viewer_code text,
        product_code text,
        payment_status text,
        report_request_json jsonb,
        report_payload_json jsonb,
        report_html text,
        report_html_url text
    )
    """,
    """
    create table if not exists reports (
        record_id text primary key references charts(record_id) on delete cascade,
        created_at timestamptz not null default now(),
        updated_at timestamptz not null default now(),
        report_preset text,
        report_addons_json jsonb,
        report_id text,
        viewer_code text,
        product_code text,
        payment_status text,
        report_request_json jsonb,
        report_payload_json jsonb,
        report_html text,
        report_html_url text
    )
    """,
    """
    create table if not exists storage_audit_runs (
        id bigserial primary key,
        created_at timestamptz not null default now(),
        scope text not null default 'durable_store',
        status text not null default 'ok',
        summary_json jsonb not null default '{}'::jsonb,
        notes text
    )
    """,
    """
    create table if not exists organizations (
        id bigserial primary key,
        created_at timestamptz not null default now(),
        updated_at timestamptz not null default now(),
        name text not null,
        slug text not null unique,
        status text not null default 'active',
        notes text
    )
    """,
    """
    create table if not exists organization_memberships (
        id bigserial primary key,
        created_at timestamptz not null default now(),
        updated_at timestamptz not null default now(),
        organization_id bigint not null references organizations(id) on delete cascade,
        counselor_id bigint references counselors(id) on delete set null,
        user_ref text,
        role text not null default 'member',
        status text not null default 'active'
    )
    """,
    """
    create table if not exists report_runs (
        id bigserial primary key,
        created_at timestamptz not null default now(),
        record_id text not null references charts(record_id) on delete cascade,
        report_id text,
        run_type text not null default 'initial_generation',
        status text not null default 'queued',
        preset text,
        addons_json jsonb not null default '[]'::jsonb,
        engine_version text,
        notes text
    )
    """,
    """
    create table if not exists report_versions (
        id bigserial primary key,
        created_at timestamptz not null default now(),
        record_id text not null references charts(record_id) on delete cascade,
        report_run_id bigint references report_runs(id) on delete set null,
        version_number integer not null default 1,
        report_payload_json jsonb,
        report_html text,
        report_html_url text,
        unique (record_id, version_number)
    )
    """,
    """
    create table if not exists access_events (
        id bigserial primary key,
        created_at timestamptz not null default now(),
        record_id text not null references charts(record_id) on delete cascade,
        event_type text not null,
        actor_type text not null,
        actor_ref text,
        metadata_json jsonb not null default '{}'::jsonb
    )
    """,
    "create index if not exists idx_charts_counselor_code on charts(counselor_code)",
    "create index if not exists idx_charts_created_at on charts(created_at desc)",
    "create index if not exists idx_reports_report_id on reports(report_id)",
    "create index if not exists idx_reports_viewer_code on reports(viewer_code)",
    "create index if not exists idx_organization_memberships_org_id on organization_memberships(organization_id)",
    "create index if not exists idx_organization_memberships_counselor_id on organization_memberships(counselor_id)",
    "create index if not exists idx_report_runs_record_id on report_runs(record_id)",
    "create index if not exists idx_report_versions_record_id on report_versions(record_id)",
    "create index if not exists idx_access_events_record_id on access_events(record_id)",
    """
    insert into counselors (name, access_code, status, notes)
    values
      ('Master Access', '7009', 'active', 'Seeded master access code'),
      ('Test Counselor', '2026', 'test', 'Seeded local 3-record limit code')
    on conflict (access_code) do nothing
    """,
]


async def ensure_database_schema(settings: AppSettings | None = None) -> bool:
    global _schema_initialized
    if _schema_initialized:
        return True

    engine = get_engine(settings=settings)
    if engine is None:
        return False

    async with engine.begin() as connection:
        for statement in SCHEMA_STATEMENTS:
            await connection.execute(text(statement))

    _schema_initialized = True
    return True


@dataclass(frozen=True)
class DatabaseStatus:
    configured: bool
    reachable: bool
    backend: str
    message: str | None = None


async def get_database_status(settings: AppSettings | None = None) -> DatabaseStatus:
    settings = settings or get_settings()
    engine = get_engine(settings=settings)
    if engine is None:
        return DatabaseStatus(
            configured=False,
            reachable=False,
            backend=settings.storage_backend,
            message="DATABASE_URL not configured",
        )

    try:
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
        return DatabaseStatus(
            configured=True,
            reachable=True,
            backend=settings.storage_backend,
            message="database reachable",
        )
    except Exception as exc:  # pragma: no cover - depends on runtime env
        return DatabaseStatus(
            configured=True,
            reachable=False,
            backend=settings.storage_backend,
            message=str(exc),
        )
