**Supabase 연결 순서**
1. Supabase 프로젝트의 `Project Settings > Database`에서 실제 DB 비밀번호를 확인하거나 재설정합니다.
2. `DATABASE_URL`의 `[YOUR-PASSWORD]` 자리에 그 비밀번호를 넣습니다.
3. `Project Settings > API`에서 필요하면 `service_role` 키를 복사해 `SUPABASE_SERVICE_ROLE_KEY`에 넣습니다.
4. [`.env.example`](/Users/essenz/Documents/Playground/astro_chart_extractor/NC/.env.example)를 기준으로 `.env`를 만듭니다.
5. `STORAGE_BACKEND`는 우선 `apps_script`로 두고, DB 이관 시 `supabase` 또는 `postgres`로 바꿀 수 있습니다.
6. FastAPI 서버를 재시작합니다.
7. `/health`에서 `database_url_configured`, `database_reachable` 값을 확인합니다.

**지금 바로 필요한 값**
- `DATABASE_URL`에 들어갈 실제 Postgres 비밀번호
- 또는 DB 대신 Supabase REST를 쓸 경우 `SUPABASE_SERVICE_ROLE_KEY`

**중요**
- 지금 주신 `publishable key`는 프론트/읽기용에 더 가깝습니다.
- FastAPI 백엔드에서 안정적으로 쓰기까지 하려면 보통 `DATABASE_URL` 또는 `service_role key`가 필요합니다.
