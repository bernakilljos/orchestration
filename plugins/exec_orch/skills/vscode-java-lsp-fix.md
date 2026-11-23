---
name: vscode-java-lsp-fix
description: |
  VSCode Java Language Server (-32097 crash) 자동 진단 및 해결.
  "Language Support for Java crashed" 감지 시 3단계 해결책 제시.
---

# VSCode Java LSP 크래시 해결 가이드

## 문제 신호 (trigger)

사용자가 다음 중 하나 언급:
- "Language Support for Java crashed"
- "-32097 error"
- "Red Hat Java extension crash"
- "LSP 죽었어"
- "Java 포트 포트 8" (random port 수정 시도)

## 근본 원인 (3가지)

| # | 원인 | 신호 | 환경 |
|---|---|---|---|
| **1** | Java extension 이 Python/Node.js 프로젝트에 활성 | 열어본 폴더가 Java 아닌데도 Java extension 시도 | VS Code 글로벌 설정이나 workspace 설정에 `java.enabled: true` |
| **2** | JDK 미설치 또는 잘못 설정 | "Cannot find jdk" 또는 포트 바인딩 실패 | Windows/Mac 에서 Java extension 이 자동 JDK 찾지 못함 |
| **3** | 포트 충돌 (이미 JDK 프로세스 돌고 있음) | 다른 VSCode 인스턴스나 IDE 가 Java LSP 포트 사용 | 멀티 IDE 또는 daemon 프로세스 |

## 해결 방법 (3단계)

### **Step 1 — Java Extension Disable (Python/Node.js 프로젝트)**

현재 폴더가 Java 프로젝트가 아니면 **Java extension 전부 disable**.

**작업**:
1. VSCode `.vscode/settings.json` 열기 (Cmd/Ctrl+K Cmd/Ctrl+S → "settings.json" 검색 → Workspace)
2. 다음 추가:
   ```json
   {
     "java.enabled": false,
     "[java]": {
       "editor.defaultFormatter": "disabled"
     }
   }
   ```
3. 저장 → VSCode 재시작 (Cmd/Ctrl+Shift+P `Developer: Reload Window`)

**결과**: Java LSP 비활성 → 크래시 0

---

### **Step 2A — Java 프로젝트면: Red Hat Java Extension Pack 완전 설치 + JDK 21**

현재 폴더가 실제 **Java 프로젝트** (pom.xml·build.gradle·.java 파일):

1. **VSCode Extension Marketplace 열기** (Activity Bar "Extensions")
2. **다음 확장 모두 설치**:
   - "Extension Pack for Java" (Red Hat) — 공식 번들
   - "Language Support for Java" (Red Hat)
   - "Debugger for Java" (Microsoft)
   - "Test Runner for Java" (Microsoft)
3. **JDK 설정**:
   - VSCode 하단 "Java 21" 버튼 클릭 → "Install JDK 21" 선택
   - 또는 수동: `.vscode/settings.json` 에:
   ```json
   {
     "java.configuration.runtimes": [
       {
         "name": "JavaSE-21",
         "path": "/path/to/jdk-21",
         "default": true
       }
     ]
   }
   ```
   (Windows: `C:\Program Files\Java\jdk-21`)
4. 저장 → 재시작

**결과**: JDK 21 + 공식 extension 번들 → LSP 안정

---

### **Step 2B — 또는: `.vscode/settings.json` 자동화**

CLI 또는 auto-script 로 한 번에 설정:

```bash
cat > .vscode/settings.json <<'EOF'
{
  "java.enabled": true,
  "java.home": null,
  "java.configuration.checkProjectSettingsExclusions": false,
  "java.configuration.updateBuildConfiguration": "automatic",
  "java.project.referencedLibraries": ["lib/**"],
  "java.jdt.ls.vmargs": "-noverify -Xmx1G -XX:+UseG1GC -XX:+UseStringDeduplication -Xms100m -Djava.rmi.server.hostname=localhost"
}
EOF
```

---

## 자동 `.vscode/settings.json` 생성 (template)

**kit 에서 자동 배포** (SessionStart hook):

- 파이썬 프로젝트 감지 (`setup.py` 또는 `pyproject.toml`) → `"java.enabled": false` 자동 등재
- Java 프로젝트 감지 (`pom.xml` 또는 `build.gradle`) → `"java.home": null` (auto-discover) 자동 등재
- 기존 settings.json 있으면 merge (키 충돌 merge strategy: existing 유지, 새 키만 추가)

**Script**: `.claude/scripts/auto-vscode-settings.py`
- Dry-run: `python auto-vscode-settings.py --dry`
- 실행: `python auto-vscode-settings.py`

---

## 검증

해결 후 확인:

```bash
# 1. LSP 구동 확인 (VSCode 콘솔)
# Cmd/Ctrl+Shift+P → "Output" → "Language Support for Java" 선택
# "Startup completed" 로그 보임 = 성공

# 2. .java 파일 열기 → 코드 완성 동작 = 성공

# 3. 포트 확인
netstat -ano | grep "6931"  # Java LSP 기본 포트
# PID 가 VSCode javac 프로세스 = 정상
```

---

## 금지 & 권장

❌ **금지**:
- Manual port 변경 (`.vscode/settings.json` 에서 `java.debug.settings.transport: "socket"` 설정) = 불안정
- JDK 버전 혼용 (Java 8 + Java 21 동시)
- Global settings 에 Java 관련 설정 (Python 프로젝트까지 영향)

✅ **권장**:
- Java 프로젝트면 **Extension Pack 공식** (Red Hat 번들)
- Python/Node.js 프로젝트면 **`java.enabled: false`** (workspace 레벨)
- 주기적 Extension 업데이트 (Red Hat 자동 수정 발표)

---

## 참조

- Red Hat Extension Pack: https://marketplace.visualstudio.com/items?itemName=vscjava.vscode-java-pack
- VSCode Java 공식 가이드: https://github.com/microsoft/vscode-java
- JDK 설치: https://www.oracle.com/java/technologies/downloads/
