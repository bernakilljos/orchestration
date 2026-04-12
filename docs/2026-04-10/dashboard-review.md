# dashboard.py 검증 결과

검증일: 2026-04-10
대상: `dashboard.py`

---

## 1. GitHub API 직접 호출(gh_get, gh_put, gh_sha) — PASS

`gh_get`, `gh_put`, `gh_sha`는 각각 69행, 82행, 100행에 함수 정의만 존재한다.
함수 정의 외부에서 직접 호출하는 곳은 없다.
- `gh_get`은 `gh_sha` 내부(102행)에서만 호출된다.
- `gh_put`은 코드 전체에서 호출되는 곳이 없다.
- `gh_sha`도 코드 전체에서 호출되는 곳이 없다.
- 모든 GitHub 연동은 `git clone` + `git push` 방식으로 전환되어 있어 API rate limit을 회피한다.

**결과: PASS** — GitHub API 직접 호출이 비즈니스 로직에서 사용되지 않음.

---

## 2. AJAX 폴링 JS 코드 문법 에러 — PASS

### make_index (552~589행)
- `quickCtrl`, `delPc`, `setInterval` 모두 표준 ES5 문법 사용.
- `fetch().then().then()` 체인 정상. 세미콜론, 괄호 매칭 이상 없음.
- Python `.format()` 미사용 (별도 변수 없이 `ajax_poll` 문자열 그대로 삽입).

### make_detail (870~957행)
- `{{`, `}}` 이중 중괄호로 Python `.format()` 이스케이프 정상 처리.
- `showTab`, `ctrl`, `sendTask`, `delTask`, `setInterval` 함수 모두 문법 정상.
- `var`/`function` 키워드 사용, ES5 호환.

### make_remote (148~281행)
- `PC_ID` 변수에 `'{pc_id}'` 삽입 (284행 `.format()` 아닌 f-string으로 body에 직접 삽입).
- `setInterval(refreshScreen, 200)` 정상.
- arrow function 1곳 (157행 `() => {{ }}`) — Python `{{`/`}}`로 이스케이프되어 JS에서 `() => { }` 정상 출력.

**결과: PASS** — JS 문법 에러 없음.

---

## 3. make_detail의 .format(pid=...) 변수 충돌 — PASS

957행: `.format(pid=urllib.parse.quote(pc_id))`

`ajax_poll` 문자열(870~957행)에서 `{pid}`는 2곳 사용:
- 871행: `var PC_ID = '{pid}';`
- 927행: `fetch('/api/detail-body/{pid}')`

나머지 모든 중괄호는 `{{`/`}}`로 이스케이프되어 있어 `.format()`과 충돌하지 않는다.
`body` 부분(703~867행)은 f-string으로 처리되므로 `.format()`의 영향을 받지 않는다.

**결과: PASS** — `{pid}` 외 다른 변수 충돌 없음.

---

## 4. git clone/push 호출의 timeout과 에러 핸들링 — PASS

모든 `subprocess.run` git 명령에 `timeout`이 지정되어 있다:

| 위치 | 명령 | timeout | 에러 핸들링 |
|------|------|---------|------------|
| 1103행 | git clone | 30s | try/finally + check=True |
| 1108행 | git add | 10s | check=True |
| 1110행 | git commit | 10s | check=True |
| 1111행 | git push | 30s | check=True |
| 1217행 | git clone | 30s | try/finally |
| 1223행 | git add | 10s | check=True |
| 1226행 | git push | 30s | check=True |
| 1377행 | git clone | 30s | try/finally + 재시도 루프 |
| 1390행 | git push | 30s | check=True |
| 1718행 | git clone | 30s | try/finally |

**결과: PASS** — 모든 git 명령에 timeout + 에러 핸들링 존재.

---

## 5. 임시 디렉토리(tempfile.mkdtemp) 정리 누락 — PASS

| 위치 | mkdtemp | rmtree | 방식 |
|------|---------|--------|------|
| 1101행 | `gh-del-` | 1113행 | `finally: shutil.rmtree(tmpdir, ignore_errors=True)` |
| 1215행 | `gh-cmd-` | 1229행 | `finally: shutil.rmtree(tmpdir, ignore_errors=True)` |
| 1375행 | `gh-url-` | 1394행 | `finally: shutil.rmtree(tmpdir, ignore_errors=True)` |
| 1716행 | `gh-poll-` | 1762행 | `finally: shutil.rmtree(tmpdir, ignore_errors=True)` |

모든 `mkdtemp` 호출에 대응하는 `finally` 블록에서 `shutil.rmtree`가 호출된다.

**결과: PASS** — 임시 디렉토리 정리 누락 없음.

---

## 6. PAT 토큰 print/로그 노출 — FAIL

### 6-1. 하드코딩된 fallback 토큰 (14행)
```python
_FALLBACK = "[REMOVED]"
```
PAT 토큰이 소스코드에 평문 하드코딩되어 있다. 환경변수 미설정 시 이 값이 사용된다.

### 6-2. repo_url에 PAT 포함 (1100, 1214, 1374, 1715행)
```python
repo_url = f"https://x:{pat}@github.com/{OWNER}/{REPO}.git"
```
`repo_url`이 `subprocess.run`에 전달되어 프로세스 인자로 노출된다.
`print`/`log`에 직접 출력하지는 않지만, subprocess 에러 발생 시 traceback에 PAT가 포함될 수 있다.

### 6-3. print 문 자체에는 PAT 미노출
`print` 호출(56, 65, 1320, 1333, 1338, 1348 등)에서 PAT 값을 직접 출력하는 곳은 없다.

**결과: FAIL**
- 하드코딩된 PAT(`_FALLBACK`)가 소스코드에 평문 존재 (보안 위험).
- `repo_url`에 PAT가 포함되어 subprocess 에러 traceback 시 노출 가능.

---

## 7. SO_REUSEADDR 적용 — WARN

1775행:
```python
srv.socket.setsockopt(__import__('socket').SOL_SOCKET, __import__('socket').SO_REUSEADDR, 1)
```

`SO_REUSEADDR`가 적용되어 있으나, `HTTPServer` 생성(1774행) 후 `serve_forever()` 호출 전에 설정된다.
`HTTPServer.__init__`에서 이미 `server_bind()`가 호출되어 bind가 완료된 상태이므로, `SO_REUSEADDR`는 bind 이전에 설정해야 효과가 있다.

올바른 방법: `HTTPServer` 서브클래스에서 `allow_reuse_address = True`를 설정하거나, `server_bind()` 호출 전에 소켓 옵션을 설정해야 한다.

**결과: WARN** — `SO_REUSEADDR` 설정 시점이 `bind()` 이후이므로 실효성이 불확실함. `HTTPServer`의 `allow_reuse_address = True` 사용 권장.

---

## 8. JPEG quality 90 — PASS

### PIL 경로 (1599행)
```python
pil_img.save(buf, format="JPEG", quality=90)
```

### PowerShell fallback 경로 (1618행)
```powershell
$ep.Param[0]=New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality,90L)
```

두 경로 모두 JPEG quality 90으로 설정되어 있다.

**결과: PASS** — JPEG quality 90 정상 적용.

---

## 9. _gh_poll_once 비동기(threading.Thread) 실행 — WARN

### 초기 1회 실행 (1764행) — 비동기
```python
threading.Thread(target=_gh_poll_once, daemon=True).start()
```
별도 스레드에서 비동기 실행된다.

### 60초 주기 반복 (1766~1770행) — 동기 (루프 스레드 내부)
```python
def _gh_poll_loop():
    while True:
        time.sleep(60)
        _gh_poll_once()  # <-- _gh_poll_loop 스레드 내에서 동기 호출
threading.Thread(target=_gh_poll_loop, daemon=True).start()
```
`_gh_poll_loop` 자체는 별도 스레드에서 실행되므로 메인 스레드를 차단하지 않는다.
그러나 `_gh_poll_once`가 `_gh_poll_loop` 스레드 내에서 동기 호출되어, git clone 실패 시 해당 스레드가 최대 30초간 블로킹된다.
메인 HTTP 서버에는 영향 없으므로 기능적 문제는 아니지만, 폴링 주기가 60초 + 실행 시간이 된다.

**결과: WARN** — 메인 스레드 비차단은 확인됨. 루프 내 동기 호출은 폴링 주기가 늘어나는 부수 효과가 있으나 심각한 문제는 아님.

---

## 종합

| # | 항목 | 결과 |
|---|------|------|
| 1 | GitHub API 직접 호출 | **PASS** |
| 2 | AJAX JS 문법 에러 | **PASS** |
| 3 | .format() 변수 충돌 | **PASS** |
| 4 | git clone/push timeout + 에러 핸들링 | **PASS** |
| 5 | 임시 디렉토리 정리 누락 | **PASS** |
| 6 | PAT 토큰 노출 | **FAIL** — 하드코딩 PAT + subprocess traceback 노출 위험 |
| 7 | SO_REUSEADDR 적용 | **WARN** — bind 이후 설정으로 실효성 불확실 |
| 8 | JPEG quality 90 | **PASS** |
| 9 | _gh_poll_once 비동기 실행 | **WARN** — 초기 1회는 비동기, 루프 내부는 동기 (메인 비차단) |

**PASS: 6건 / WARN: 2건 / FAIL: 1건**
