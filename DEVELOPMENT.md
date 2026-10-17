# 개발

이 문서는 plugin 저장소를 수정하거나 배포 묶음을 만드는 개발자용입니다. 설치와 사용법은 [README.md](README.md)를 봅니다.

## 목차

- 빌드와 검증
- 번들 구성
- 스킬 목록과 도구 참조
- 연결된 도구와 snapshot
- 로컬에서 시험하기

## 빌드와 검증

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build.py
```

빌드는 스킬 목록·경로·메타데이터, 문서 링크, 구현 tool/schema snapshot, 워크플로 required/optional capability, JSON 예제 입력 schema, 호스트 설정과 버전 일치를 검증합니다. `scripts/build.py --mcp-root <mcp-checkout>` 또는 `scripts/build.py --manifest <manifest.json>`을 주면 pinned MCP manifest와 tool schema digest도 대조합니다. 번들된 [구현 도구 스냅샷](references/implemented-tools.snapshot.json)은 원본 MCP commit·manifest digest와 각 입력 schema digest를 기록합니다.

## 번들 구성

- `dist/vox-ai-plugin.zip`: 호스트 manifest, MCP 연결 설정, 스킬과 공통 문서.
- `dist/vox-ai-skills.zip`: 같은 스킬과 공통 문서. 연결 설정과 호스트 manifest는 제외.
- `bundle-manifest.json`: 공통 파일별 SHA-256과 묶음 digest.

공통 digest는 스킬과 공통 문서만 대상으로 하며 ZIP 전체나 연결 설정의 digest가 아닙니다.
CI는 테스트와 빌드를 실행하고 커밋된 bundle manifest가 최신인지 확인합니다.
배포 변경 시 두 호스트 manifest의 버전을 함께 올리고 빌드해 bundle manifest를 갱신합니다.

## 스킬 목록과 도구 참조

전체 스킬 목록은 [catalog.json](catalog.json)에 있습니다. 각 스킬의 `tools.implemented`는 현재 snapshot에서 실행 가능한 도구이고 `tools.designed_only`는 지침에 남아 있는 설계 참조입니다. 상단 `designed_tool_references`가 해당 참조의 전체 목록입니다. 실행 원칙은 [execution-contract.md](references/execution-contract.md)에 있습니다.

## 연결된 도구와 snapshot

설치 후 연결된 서버의 도구 목록과 입력 스키마를 확인합니다. 번들에는 첫 배포 범위 도구(조직·agent·버전·템플릿·Manual·도구·지식·번호·통화·캠페인·시트·고객)의 schema 후보가 있습니다. 실제 호스트의 노출 도구와 권한은 다를 수 있습니다. workflow별 capability는 [workflow-capabilities.json](references/workflow-capabilities.json), 입력 schema와 출처 상태는 [implemented-tools.snapshot.json](references/implemented-tools.snapshot.json)에 있습니다.

## 로컬에서 시험하기

로컬 변경을 시험하려면 marketplace 추가 명령에 복제한 저장소의 절대 경로를 지정합니다.

```text
/plugin marketplace add <복제한 저장소의 절대 경로>
```

```sh
codex plugin marketplace add <복제한 저장소의 절대 경로>
grok plugin marketplace add <복제한 저장소의 절대 경로>
```
