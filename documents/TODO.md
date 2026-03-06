# TODOs

## Test

- [ ] test 코드 작성 및 실행 검증

## Lint

- [ ] pre-commit 적용하기

## API (MVP)

- [O] 종목 검색 API (`/stock/search`)
  - [ ] **한글 회사명 검색 지원** (추후 구현)
    - Yahoo Finance API는 한글 검색 미지원 (400 Bad Request)

## QA

- [ ] Token 만료시 자동으로 refresh하는 로직 추가.
- [ ] Cache를 적극적으로 활용해서 비용 최적화하기.
