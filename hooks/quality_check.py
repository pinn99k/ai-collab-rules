"""ai-collab 품질 경보 (pre-commit).

이번 커밋에서 새로 생긴 것만 본다. 경고만 하고 커밋은 막지 않는다.
- 순환 복잡도(CC) 10 초과 함수가 새로 생기거나 10을 넘게 된 경우 (lizard)
- 변경 파일에 새 중복 블록이 생긴 경우 (jscpd)
- LOC 증가가 사전 예상의 2배를 넘은 경우 (.git/ai-estimate에 적힌 숫자)
출력은 최대 3줄. 경보가 없으면 아무것도 출력하지 않는다.
"""
import csv, io, json, os, shutil, subprocess, sys, tarfile, tempfile

CODE_EXT = {".js", ".jsx", ".ts", ".tsx", ".java", ".py", ".c", ".h", ".cpp"}
CC_LIMIT = 10
LOC_FACTOR = 2


def git(*args, binary=False):
    r = subprocess.run(["git", *args], capture_output=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def staged_code_files():
    out = git("diff", "--cached", "--name-only", "--diff-filter=AM")
    return [f for f in out.splitlines() if os.path.splitext(f)[1] in CODE_EXT]


def export_index(dst):
    subprocess.run(["git", "checkout-index", "-a", "--prefix=" + dst.replace("\\", "/") + "/"], check=True)


def export_head(dst):
    data = git("archive", "HEAD", binary=True)
    if not data:
        return False  # 첫 커밋
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
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


def duplicate_count(tree, files, npx):
    out = os.path.join(tree, ".jscpd-out")
    subprocess.run([npx, "--yes", "jscpd", "--silent", "--reporters", "json", "--output", out, "."],
                   cwd=tree, capture_output=True, shell=(os.name == "nt"))
    report = os.path.join(out, "jscpd-report.json")
    if not os.path.exists(report):
        return 0
    targets = {f.replace("\\", "/") for f in files}
    dups = json.load(open(report, encoding="utf-8")).get("duplicates", [])
    def hit(d):
        names = {os.path.relpath(d[k]["name"], tree).replace("\\", "/") if os.path.isabs(d[k]["name"])
                 else d[k]["name"].replace("\\", "/").lstrip("./") for k in ("firstFile", "secondFile")}
        return bool(names & targets)
    return sum(1 for d in dups if hit(d))


def loc_delta(files):
    total = 0
    for line in git("diff", "--cached", "--numstat", "--", *files).splitlines():
        a, d, _ = line.split("\t", 2)
        if a != "-":
            total += int(a) - int(d)
    return total


def read_estimate():
    path = os.path.join(git("rev-parse", "--git-dir").strip(), "ai-estimate")
    try:
        return int(open(path, encoding="utf-8").read().strip())
    except (OSError, ValueError):
        return None


def main():
    files = staged_code_files()
    if not files:
        return
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
            diff = duplicate_count(new, files, npx) - (duplicate_count(old, files, npx) if has_head else 0)
            if diff > 0:
                alarms.append(f"새 중복 블록 {diff}개 (변경 파일 관련)")
        else:
            notes.append("npx 없음: 중복 검사 생략 (Node.js 필요)")

    est = read_estimate()
    delta = loc_delta(files)
    if est and delta > est * LOC_FACTOR:
        alarms.append(f"LOC +{delta}, 예상 {est}의 {LOC_FACTOR}배 초과")

    lines = [f"[ai-collab 경보] {a}" for a in alarms]
    if alarms:
        lines[-1] += " → explain-back 대상"
        log = os.path.join(git("rev-parse", "--git-dir").strip(), "ai-alarms.log")
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(" | ".join(alarms) + "\n")
    lines += [f"[ai-collab] {n}" for n in notes]
    if lines:
        print("\n".join(lines[:3]))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # 경보 스크립트 오류로 커밋을 막지 않는다
        print(f"[ai-collab] 검사 건너뜀: {e}")
