"""합성 예제 검증 결과를 JSON으로 기록한다."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,unittest

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent/'tests'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'kind':'synthetic regression tests',
            'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'status':'PASS' if result.wasSuccessful() else 'FAIL',
            'scope':'현재 논문 공개 범위의 전처리·MATTR·출처 집합·통계 함수·데이터 구조 합성 검증. 실제 데이터 검증과 별개.'}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__=='__main__':main()
