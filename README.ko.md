# 한국어 AI 협업 글쓰기 분석 코드와 익명화 분석 자료

[English](README.md) · [변수 설명](DATA_DICTIONARY.ko.md) · [자료 공개 범위](DATA_AVAILABILITY.md)

저자: **유환일** · 성균관대학교 · [ORCID](https://orcid.org/0009-0000-9116-9810)

이 저장소는 논문의 분석 범위에 해당하는 Python 코드와 익명화된 수치·범주 자료를 제공한다. 공개 범위 점검일: **2026-11-14**.

## 연구 자료와 지표

연구 자료는 중급 한국어 학습자 28명이 2026학년도 1학기에 자기소개, 중고 거래, SNS 게시글 과제를 수행하며 작성한 글이다. 과제마다 학습자 초고(A), AI 생성본(B), 협력 수정을 거친 최종본(C)이 있으며, 전체 규모는 84개 과제, 252편의 텍스트, 802개의 의미 코딩 단위이다. A는 B보다 먼저 작성되었다. 사용한 AI 도구와 프롬프트, A를 AI에 입력했는지 여부는 따로 통제하지 않았다. 따라서 B가 A와 무관하게 생성되었다고 가정하지 않는다.

논문에서 보고하는 F1~F3 자동 산출 지표는 다음 **6개**이다.

| 평가 항목 | 지표 | 지표 수 |
| --- | --- | ---: |
| F1 산출 유창성 | 문자 수·어절 수·문장 수 | 3 |
| F2 어휘 다양성 | MATTR20 | 1 |
| F3 통사 복잡성 | 평균 문장 길이·문장당 서술어 수 | 2 |
| 합계 | | 6 |

F4는 수동으로 코딩한 문법 오류를 100어절당 개수로 나타낸 지표이다. F5~F8은 형태와 출처의 대응 관계를 측정한다. F9는 의미 단위마다 대표 정보 조정 코드를 하나씩 부여하고, F10은 표현 조정 코드를 여러 개 부여할 수 있다. **A/B 공통**은 C의 명제가 A와 B에 모두 나타나는 경우를 가리킨다. **통합**은 명제와 명제 간 관계를 포함하여 두 버전의 내용 요소를 결합한 경우를 말하며, 각 버전에만 있는 정보로 한정하지 않는다. 기존 코딩값은 그대로 유지하였다.

## 파일 구성과 실행 방법

| 경로 | 내용 |
| --- | --- |
| `data/text_metrics.csv` | 텍스트 252편별 익명화 키, 논문의 자동 산출 지표 6개, 기존에 코딩한 문법 오류율과 오류 수, 단문 규칙 적용 여부 |
| `data/source_metrics.csv` | 과제 84개별 F5~F8 비율과 관련 유형 수 |
| `data/meaning_codes.csv` | 의미 단위 802개의 익명화 키, 의미 출처, F9/F10 코드(원문과 자유 서술 메모는 제외) |
| `paper_metrics.py`, `reproduce.py` | 논문 범위의 전처리 및 별도 사용 권한을 받은 외부 원문의 지표 산출 |
| `rq1_reproduce.py`, `rq2_reproduce.py`, `public_statistics.py` | 공개된 수치·범주 자료를 이용한 통계 분석 재현 |
| `reference/aggregates/` | 논문 범위의 참조 결과표(기존에 보고한 전체 검정의 보정 p값은 참조용으로만 제공) |
| `reference/public_replay/` | 공개용 참여자 순서에 따른 BCa 기준 결과 |
| `tests/`, `validation/` | 현재 공개 범위에 대한 검증 결과와 실행 기록 |
| `SHA256SUMS.json`, `파일검증.py` | 배포 파일의 무결성 검사 |

Python 3.12 사용을 권장하며, 아래 명령은 패키지 최상위 폴더에서 실행한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -B 파일검증.py
python -B 검증실행.py --output new_run/synthetic-tests.json
python -B public_statistics.py --output new_run/statistics
```

Windows PowerShell에서는 `.venv\Scripts\Activate.ps1`로 가상환경을 활성화한다. 출력 폴더는 아직 존재하지 않는 새 경로로 지정해야 한다. 통계 재현을 실행하면 표 13개와 `validation_report.json`이 생성된다. 이 과정에서 원문에 대한 NLP 재측정이나 수동 코딩 재판정은 이루어지지 않는다.

원문 사용 권한을 별도로 받은 경우에는 익명화된 `participant_id`·`task_id`, `genre`, `A_text`·`B_text`·`C_text` 열을 포함한 외부 CSV 파일로 지표를 산출할 수 있다. `A_manual_error_count`·`B_manual_error_count`·`C_manual_error_count` 열은 선택 사항이다. 이 입력 파일은 배포 대상에 포함되지 않는다.

```bash
python -B reproduce.py --input "/path/to/restricted-pseudonymized-texts.csv" --output new_run/measurement
```

이 명령은 입력 파일을 수정하지 않으며 수치 요약만 출력한다. 제한 자료인 원문은 공개 저장소에 추가해서는 안 된다. 이 공개 패키지는 학습자 원문 말뭉치가 아니다. 공개 예시에 전화번호를 적어야 할 때는 `010-0000-0000`을 사용한다.

## 재계산 범위와 한계

지표는 먼저 텍스트별로 산출한다. 이어서 학습자마다 세 과제의 값을 버전(A·B·C)별로 동일한 가중치를 두어 산술평균하고, 이를 28명의 반복측정 자료로 사용한다. 텍스트를 이어 붙여 다시 측정하지는 않는다. 오류율 역시 텍스트별로 산출한 비율의 평균이며, 오류 수와 어절 수를 각각 합산하여 계산한 비율과는 다르다. 과제 간 비교에는 학습자별 C−A 변화량을 사용한다.

F1~F3은 Mauchly 구형성 검정 결과에 따라 Greenhouse–Geisser 보정을 적용하는 반복측정 분산분석(ANOVA)으로 분석하고, F4는 Friedman 검정과 Wilcoxon 사후검정으로 분석한다.

F5·F6·F7은 분모가 각각 A 고유 유형, B 고유 유형, C 전체 유형으로 서로 다르므로 합이 100%가 되는 구성비가 아니다. F8은 `(RB−RA)/(RB+RA)`로 정의하며, 분모가 0인 경우와 결측값은 코드에 명시된 규칙에 따라 처리한다. 형태 바이그램은 문장부호를 제거한 뒤 추출한 형태소 표면형·품사 쌍의 고유 유형 집합이며, 문장 경계를 넘어 구성될 수 있다.

RQ2의 BCa 신뢰구간은 20,000회 재표집과 시드값 20260820으로 산출한다. 공개용으로 참여자 순서를 무작위화하였기 때문에 유한 몬테카를로 재표집 결과가 달라지며, 이로 인해 신뢰구간 끝점 8개가 기존 참조값과 차이를 보인다(최대 절대차 0.0031929721). 기존 참조값은 그대로 보존하고, 공개 순서에 따른 기준 결과는 별도로 검증한다. 계산 결과가 일치한다고 해서 수동 코딩의 타당성, 코더 간 신뢰도, 교육적 인과 효과가 입증되는 것은 아니다.

## 라이선스와 인용

실행 코드에는 [MIT](LICENSE) 라이선스를, 익명화 분석 자료·표·검증 기록·설명 문서에는 [CC BY 4.0](LICENSE-DATA.md) 라이선스를 적용한다. 공개하지 않은 원본 학습자 자료에는 이 라이선스가 적용되지 않는다. 인용 메타데이터는 [CITATION.cff](CITATION.cff)에서 확인할 수 있다.

> Liu, H.-Y. (2026). *Korean AI collaborative writing analysis: Code and pseudonymized analytical data* (Version 1.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.24191921

본문 인용은 **Liu(2026)** 또는 **(Liu, 2026)**으로 표기한다. 연구 결과를 언급할 때는 관련 학술지 논문을 별도로 인용한다.
