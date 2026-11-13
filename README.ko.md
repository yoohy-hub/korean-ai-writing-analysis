# 한국어 AI 협업 글쓰기 분석 코드와 가명 분석 자료

[English](README.md) · [변수 설명](DATA_DICTIONARY.ko.md) · [자료 공개 범위](DATA_AVAILABILITY.md)

저자: **유환일** · 성균관대학교 · [ORCID](https://orcid.org/0009-0000-9116-9810)

논문의 분석 범위에 해당하는 Python 코드와 익명화 데이터를 제공한다. 공개 범위 점검일: **2026-11-14**.

## 연구 자료와 논문의 지표

자료는 2026학년도 1학기 중급 한국어 학습자 28명이 자기소개·중고거래·SNS 과제를 수행하며 작성한 초고(A), AI 생성본(B), 협력 수정 최종본(C)으로 구성된다. 총 84과제·252텍스트이며 의미 코딩은 802단위이다. A를 먼저 작성하였고, AI 도구·프롬프트와 A 입력 여부를 별도로 통제하지 않았다.

논문의 F1~F3 자동 산출 지표는 정확히 다음 **6개**이다.

| 평가 항목 | 지표 | 지표 수 |
| --- | --- | ---: |
| F1 산출 유창성 | 문자 수·어절 수·문장 수 | 3 |
| F2 어휘 다양성 | MATTR20 | 1 |
| F3 통사 복잡성 | 평균 문장 길이·문장당 서술어 수 | 2 |
| 합계 | | 6 |

F4는 기존 수동 코딩에 기초한 100어절당 문법 오류율이다. F5~F8은 형태 출처의 대응을 측정한다. F9는 의미 단위당 하나의 대표 정보 조정 코드이고 F10은 복수 표현 조정 코드이다. **공통**은 C의 명제가 A와 B 모두에 있는 경우, **통합**은 명제와 명제 관계를 포함한 두 버전의 내용 요소를 결합한 경우이다.

## 구성과 실행

| 경로 | 내용 |
| --- | --- |
| `data/text_metrics.csv` | 252텍스트의 가명 키·논문 자동 지표 6개·기존 문법 오류율과 오류 수·단문 처리 상태 |
| `data/source_metrics.csv` | 84과제의 F5~F8 비율과 관련 유형 수 |
| `data/meaning_codes.csv` | 802단위의 가명 키·의미 출처·F9/F10 코드. 원문과 자유서술은 제외 |
| `paper_metrics.py`, `reproduce.py` | 논문 범위의 전처리와 권한 있는 외부 원문 지표 산출 |
| `rq1_reproduce.py`, `rq2_reproduce.py`, `public_statistics.py` | 공개 수치·범주 자료의 통계 재계산 |
| `reference/aggregates/` | 논문 범위의 참조표. 기보고 전체검정 보정 p값은 참조 전용 |
| `reference/public_replay/` | 공개 가명 순서에 따른 BCa 기준 |
| `tests/`, `validation/` | 현재 공개 범위의 검증과 실행 기록 |
| `SHA256SUMS.json`, `파일검증.py` | 배포 파일 무결성 검사 |

Python 3.12를 권장하며 폴더 최상위에서 실행한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -B 파일검증.py
python -B 검증실행.py --output new_run/synthetic-tests.json
python -B public_statistics.py --output new_run/statistics
```

Windows PowerShell에서는 `.venv\Scripts\Activate.ps1`로 활성화한다. 출력 폴더는 새 경로여야 한다. 통계 실행은 표 13개와 `validation_report.json`을 생성한다. 원문 NLP 재측정과 수동 코딩 재판정은 하지 않는다.

권한 있는 원문을 별도로 보유한 경우, 가명 `participant_id`·`task_id`, `genre`, `A_text`·`B_text`·`C_text`가 있는 외부 CSV를 사용할 수 있다. 선택 열은 `A_manual_error_count`·`B_manual_error_count`·`C_manual_error_count`이다. 이 입력은 배포하지 않는다.

```bash
python -B reproduce.py --input "/path/to/restricted-pseudonymized-texts.csv" --output new_run/measurement
```

이 명령은 입력을 변경하지 않고 수치 요약만 내보낸다. 원문을 공개 저장소에 추가해서는 안 된다. 공개본은 학습자 원문 말뭉치가 아니다. 공개 예시에 전화번호가 필요하면 `010-0000-0000`을 사용한다.

## 재계산 범위와 한계

각 텍스트의 지표를 먼저 구한 뒤, 학습자별 세 과제의 값을 A·B·C별로 동일 가중치로 산술평균하여 28명의 반복측정 자료를 구성한다. 텍스트를 합쳐 재측정하지 않는다. 오류율도 개별 텍스트에서 산출한 비율의 평균이며, 오류 수와 어절 수를 각각 합산해 계산한 비율과 구별된다. 주제 비교는 학습자별 C−A 변화량을 사용한다.

공개 코드는 점추정, 전체검정의 다중검정 보정 전 p값(필요 시 Greenhouse–Geisser 보정 적용), 지표 내 세 쌍의 사후검정과 그 Holm 보정을 독립적으로 재계산한다. **논문에 기보고된 전체검정의 보정 p값은 참조표에만 보존하며, 공개 코드의 재계산 및 독립적 일치 검증 대상에서 제외한다.** 참조 전용 값을 새로 추정한 결과로 해석해서는 안 된다.

F1~F3에는 Mauchly 구형성 검정과 Greenhouse–Geisser 보정 규칙을 적용한 반복측정 ANOVA를, F4에는 Friedman 검정과 Wilcoxon 사후검정을 사용한다. MATTR20은 20형태소 창을 사용하며 1~19형태소는 전체 TTR, 0형태소는 결측값으로 처리한다. 실제 단문 대체는 1편이다. Kiwi가 수동 문법 오류의 정답을 자동 생성한 것은 아니다.

F5·F6·F7의 분모는 각각 A 고유 유형·B 고유 유형·C 전체 유형으로 다르므로 합계 100%인 구성비가 아니다. F8은 `(RB−RA)/(RB+RA)`이며 영분모·결측 처리는 코드에 따른다. 형태 바이그램은 문장부호 제거 후의 형태소·품사 고유 유형 집합으로 문장 경계를 가로지를 수 있다.

RQ2 BCa는 20,000회 재표집과 seed 20260820을 사용한다. 무작위 가명 순서에서는 유한 재표집의 신뢰구간 끝점 8개가 기존 참조와 다르며 최대 절대차는 0.0031929721이다. 원 참조는 보존하고 공개 순서 기준을 별도로 검증한다. 계산 검증은 수동 판정의 타당성·코더 간 신뢰도·교육적 인과 효과의 인증이 아니다.

## 라이선스와 인용

코드는 [MIT](LICENSE), 가명 분석 자료·표·검증 기록·설명서는 [CC BY 4.0](LICENSE-DATA.md)이다. 공개하지 않은 원본 자료에는 이 허락이 적용되지 않는다. 인용 메타데이터는 [CITATION.cff](CITATION.cff)에 있다.

> Liu, H.-Y. (2026). *Korean AI collaborative writing analysis: Code and pseudonymized analytical data* (Version 1.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.24191921

본문 인용은 **Liu(2026)** 또는 **(Liu, 2026)**으로 표기한다. 관련 학술지 논문은 해당 논문의 서지 정보로 별도 인용한다.
