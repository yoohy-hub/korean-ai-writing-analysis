"""배포 파일의 SHA-256을 검증한다. 실행 중 생긴 새 결과 파일은 대상이 아니다."""
from pathlib import Path
import hashlib,json,sys

def main():
    root=Path(__file__).resolve().parent
    manifest=json.loads((root/'SHA256SUMS.json').read_text(encoding='utf-8'))
    bad=[]
    for name,expected in manifest['files'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            bad.append(name+': 누락 또는 잘못된 경로');continue
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            bad.append(name+': 변경됨')
    print(json.dumps({'status':'FAIL' if bad else 'PASS','checked_files':len(manifest['files']),'issues':bad},ensure_ascii=False,indent=2))
    return 1 if bad else 0

if __name__=='__main__':sys.exit(main())
