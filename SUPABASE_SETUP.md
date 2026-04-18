**Supabase 연결 순서**
1. Supabase 프로젝트의 `Project Settings > Database`에서 실제 DB 비밀번호를 확인하거나 재설정합니다.
2. `DATABASE_URL`의 `[YOUR-PASSWORD]` 자리에 그 비밀번호를 넣습니다.
3. `Project Settings > API`에서 필요하면 `service_role` 키를 복사해 `SUPABASE_SERVICE_ROLE_KEY`에 넣습니다.
4. [`.env.example`](/Users/essenz/Documents/Playground/astro_chart_extractor/NC/.env.example)를 기준으로 `.env`를 만듭니다.
5. `STORAGE_BACKEND`는 계속 `apps_script`로 두고, Supabase/Postgres는 Phase 1 기준 `active durable mirror + B2B foundation store`로 운영합니다.
6. FastAPI 서버를 재시작합니다.
7. `/health`에서 연결 기본 상태를 확인하고, `/api/storage/audit`에서 `database.state`, `blocking_reason`, `next_action`, `reachability_gate_passed`와 실제 durable-store row count를 확인합니다.
8. `/api/storage/reconcile`에서 Apps Script ↔ Postgres `record_id` 기준 parity audit를 읽기 전용으로 확인합니다.

**Phase 1에서 추가되는 Postgres 역할**
- `charts`, `reports`, `counselors`의 durable mirror 유지
- `storage_audit_runs`, `organizations`, `organization_memberships`, `report_runs`, `report_versions`, `access_events` foundation schema 준비
- dual-write 결과를 Apps Script only / Postgres only / both / neither 수준으로 더 명확히 관찰
- read-only reconciliation route를 통해 record_id 기준 parity drift를 빠르게 확인

**운영자 메모**
- 상담/운영팀의 가장 쉬운 수기 관리 surface는 여전히 Sheets / Apps Script입니다.
- Supabase/Postgres는 백업, 감사, 향후 B2B 확장을 위한 backend layer로 강화하는 단계이며, 지금 배치에서 primary hub로 승격하지 않습니다.

**지금 바로 필요한 값**
- `DATABASE_URL`에 들어갈 실제 Postgres 비밀번호
- 또는 DB 대신 Supabase REST를 쓸 경우 `SUPABASE_SERVICE_ROLE_KEY`

**중요**
- 지금 주신 `publishable key`는 프론트/읽기용에 더 가깝습니다.
- FastAPI 백엔드에서 안정적으로 쓰기까지 하려면 보통 `DATABASE_URL` 또는 `service_role key`가 필요합니다.
- Supabase primary promotion은 parity verification, reconciliation tooling, `NCreports` read-path strategy, rollback plan이 준비된 뒤에만 검토합니다.
