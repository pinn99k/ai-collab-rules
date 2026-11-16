"""ai-collab 품질 경보 (pre-commit).

이번 커밋에서 새로 생긴 것만 본다. 경고만 하고 커밋은 막지 않는다.
- 순환 복잡도(CC) 10 초과 함수가 새로 생기거나 10을 넘게 된 경우 (lizard)
- 변경 파일에 새 중복 블록이 생긴 경우 (jscpd). 양쪽이 모두 테스트 파일이면 세지 않는다
- 소스 줄 수 증가가 사전 예상의 2배를 넘은 경우 (.git/ai-estimate에 적힌 숫자, 비교 후 지운다)
경보와 안내는 최대 3줄. docs/explain-log.md에 대기가 있으면 대기 수 한 줄을 더한다.
"""
import csv, io, json, os, shutil, subprocess, sys, tarfile, tempfile
from datetime import datetime

CODE_EXT = {".js", ".jsx", ".ts", ".tsx", ".java", ".py", ".c", ".h", ".cpp"}
CC_LIMIT = 10
LOC_FACTOR = 2
TOOL_DIR = "ai-collab-rules/"  # 협업 도구 자체 코드는 검사하지 않는다
TEST_MARKS = (".test.", ".spec.", "_test.", "/test/", "/tests/", "/__tests__/")
PENDING = "대기"


def git(*args, binary=False):
    r = subprocess.run(["git", *args], capture_output=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def is_test(path):
    p = "/" + path.replace("\\", "/")
    return any(m in p for m in TEST_MARKS) or os.path.basename(p).startswith("test_")


def staged_code_files():
    out = git("diff", "--cached", "--name-only", "--diff-filter=AM")
    return [f for f in out.splitlines()
            if os.path.splitext(f)[1] in CODE_EXT and not f.startswith(TOOL_DIR)]


def export_index(dst):
    subprocess.run(["git", "checkout-index", "-a", "--prefix=" + dst.replace("\\", "/") + "/"], check=True)


def export_head(dst):
    data = git("archive", "HEAD", binary=True)
    if not data:
        return False  # 첫 커밋
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        try:
            t.extractall(dst, filter="data")
        except TypeError:  # filter 인자가 없는 Python
            t.extractall(dst)
    return True


def over_limit_functions(tree, files):
    paths = [f for f in files if os.path.exists(os.path.join(tree, f))]
    if not paths:
        return {}
    r = subprocess.run([sys.executable, "-m", "lizard", "--csv", *paths], cwd=tree, capture_output=True)
    found = {}
    for row in csv.reader(io.StringIO(r.stdout.decode("utf-8", "replace"))):
        if len(row) >= 8 and row[1].isdigit() and int(row[1]) > CC_LIMIT:
            found[(row[6].replace("\\", "/"), row[7])] = int(row[1])
    return found


def duplicates(tree, files, npx):
    """변경 파일에 걸친 중복 블록을 {내용: 위치}로 돌려준다. 양쪽이 모두 테스트 파일이면 뺀다."""
    out = os.path.join(tree, ".jscpd-out")
    subprocess.run([npx, "--yes", "jscpd", "--silent", "--reporters", "json", "--output", out, "."],
                   cwd=tree, capture_output=True, shell=(os.name == "nt"))
    report = os.path.join(out, "jscpd-report.json")
    if not os.path.exists(report):
        return {}
    targets = {f.replace("\\", "/") for f in files}

    def name(side):
        n = side["name"]
        n = os.path.relpath(n, tree) if os.path.isabs(n) else n
        n = n.replace("\\", "/")
        return n[2:] if n.startswith("./") else n

    found = {}
    for d in json.load(open(report, encoding="utf-8")).get("duplicates", []):
        a, b = name(d["firstFile"]), name(d["secondFile"])
        if not ({a, b} & targets) or (is_test(a) and is_test(b)):
            continue
        where = f"{a}:{d['firstFile'].get('start', '?')} ↔ {b}:{d['secondFile'].get('start', '?')}"
        # 내용으로 구분한다. 코드를 옮기기만 한 것은 새 중복으로 세지 않는다
        found[d.get("fragment") or where] = where
    return found


def loc_delta(files):
    """(소스 증가, 테스트 증가)"""
    src = test = 0
    for line in git("diff", "--cached", "--numstat", "--", *files).splitlines():
        a, d, path = line.split("\t", 2)
        if a == "-":
            continue
        if is_test(path):
            test += int(a) - int(d)
        else:
            src += int(a) - int(d)
    return src, test


def take_estimate():
    """예상 줄 수를 읽고 지운다. 지난 예상치가 다음 커밋에 남지 않게 한다."""
    path = os.path.join(git("rev-parse", "--git-dir").strip(), "ai-estimate")
    try:
        value = int(open(path, encoding="utf-8").read().strip())
    except (OSError, ValueError):
        value = None
    try:
        os.remove(path)
    except OSError:
        pass
    return value


def pending_count():
    """docs/explain-log.md에서 상태 칸이 '대기'인 줄 수."""
    top = git("rev-parse", "--show-toplevel").strip()
    try:
        text = open(os.path.join(top, "docs", "explain-log.md"), encoding="utf-8").read()
    except OSError:
        return 0
    return sum(1 for line in text.splitlines()
               if any(cell.strip() == PENDING for cell in line.split("|")[2:]))


def check(files):
    alarms, notes = [], []
    with tempfile.TemporaryDirectory() as tmp:
        new, old = os.path.join(tmp, "new"), os.path.join(tmp, "old")
        os.makedirs(new); os.makedirs(old)
        export_index(new)
        has_head = export_head(old)

        try:
            import lizard  # noqa: F401
            now, before = over_limit_functions(new, files), over_limit_functions(old, files) if has_head else {}
            added = {k: v for k, v in now.items() if k not in before}
            if added:
                (f, fn), cc = next(iter(added.items()))
                more = f" 외 {len(added) - 1}개" if len(added) > 1 else ""
                alarms.append(f"CC>{CC_LIMIT} 함수 새로 생김: {f} {fn} (CC {cc}){more}")
        except ImportError:
            notes.append("lizard 없음: pip install lizard")

        npx = shutil.which("npx")
        if npx:
            now = duplicates(new, files, npx)
            before = duplicates(old, files, npx) if has_head else {}
            added = [where for key, where in now.items() if key not in before]
            if added:
                more = f" 외 {len(added) - 1}개" if len(added) > 1 else ""
                alarms.append(f"새 중복 블록 {len(added)}개: {added[0]}{more}")
        else:
            notes.append("npx 없음: 중복 검사 생략 (Node.js 필요)")

    est = take_estimate()
    src, test = loc_delta(files)
    if est and src > est * LOC_FACTOR:
        alarms.append(f"LOC 소스 +{src} (테스트 +{test}), 예상 {est}의 {LOC_FACTOR}배 초과")
    elif est is None and src > 0:
        notes.append("예상 줄 수 없음: 구현 전에 .git/ai-estimate에 숫자를 적는다")

    lines = [f"[ai-collab 경보] {a}" for a in alarms]
    if alarms:
        lines[-1] += " → explain-back 대상"
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        branch = git("symbolic-ref", "--short", "-q", "HEAD").strip() or "?"
        log = os.path.join(git("rev-parse", "--git-dir").strip(), "ai-alarms.log")
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(f"{stamp} | {branch} | " + " | ".join(alarms) + "\n")
    lines += [f"[ai-collab] {n}" for n in notes]
    return lines[:3]


def main():
    files = staged_code_files()
    lines = check(files) if files else []
    waiting = pending_count()
    if waiting:
        lines.append(f"[ai-collab] explain-back {PENDING} {waiting}건")
    if lines:
        print("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # 경보 스크립트 오류로 커밋을 막지 않는다
        print(f"[ai-collab] 검사 건너뜀: {e}")
