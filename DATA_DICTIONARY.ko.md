# 공개 분석 자료 변수 설명

세 CSV는 논문 분석 범위의 수치·범주 자료이며 원문은 포함하지 않는다. 보존한 측정값과 판정값은 변경하지 않았다. 빈 셀은 결측값이며 0으로 대체하지 않는다.

## 공통 키

- `participant_id`: 28명의 무작위 가명 키.
- `task_id`: 학습자×주제 84과제의 무작위 가명 키.
- `genre`: 자기소개서·중고거래 글·SNS 글.
- `version`: A 초고·B AI 생성본·C 협력 수정 최종본.
- `unit_id`: 의미 단위의 무작위 가명 키.

## text_metrics.csv — 252행

| 열 | 내용 |
| --- | --- |
| characters | F1 문자·숫자 수 |
| eojeols | F1 한글·영문·숫자를 포함한 공백 단위 어절 수 |
| sentences | F1 Kiwi 문장 수 |
| mattr20 | F2 20형태소 창의 유형/토큰 평균. 단문은 TTR |
| mean_sentence_length | F3 문장당 어절 수 |
| predicates_per_sentence | F3 문장당 서술어 수 |
| manual_errors_per_100_eojeols | F4 기존 수동 문법 오류의 100어절당 비율 |
| manual_error_count | 기존 수동 문법 오류 수 |
| mattr_short_ttr | 단문 TTR 대체 여부 |

F1~F3 자동 지표는 총 6개이다. 오류 수와 단문 상태는 지표 산출을 설명하는 값이며 별도의 자동 지표로 세지 않는다.

## source_metrics.csv — 84행

`retention_ra`, `borrowing_rb`, `novelty_nc`는 0~1 비율이고 `proximity_p`는 `(RB−RA)/(RB+RA)`이다. `a_unique_bigrams`, `b_unique_bigrams`, `c_bigrams`는 각 분모의 유형 수, `a_retained_bigrams`, `b_borrowed_bigrams`, `c_new_bigrams`는 각 분자의 유형 수이다. 개별 원문 바이그램은 배포하지 않는다.

## meaning_codes.csv — 802행

`meaning_source`는 기존 의미 출처 판정, `f9`는 단위별 하나의 대표 정보 조정 코드, `f10_codes`는 `|`로 구분한 복수 표현 조정 코드이다. 같은 단위의 중복 F10 코드는 한 번만 센다. 원문·대응문·자유서술·이름 대응표는 제외하였다. 공통과 통합의 구분은 README를 참조한다.

## 참조 통계

기보고 전체검정 보정 p값은 `reference/aggregates/`의 참조값이다. 공개 재계산 및 독립 일치 검증 대상에서 제외하며, 새로 추정한 값으로 해석하지 않는다.
