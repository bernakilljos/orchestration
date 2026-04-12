# setup.exe 빌드 방법

## 1. Inno Setup 설치

```
winget install JRSoftware.InnoSetup
```

또는 https://jrsoftware.org/isdl.php 에서 다운로드

## 2. setup.exe 컴파일

### GUI로 컴파일
1. `setup.iss` 파일을 더블클릭 (Inno Setup Compiler 열림)
2. Build > Compile (Ctrl+F9)
3. `setup\Output\OrchestrationKit-Setup.exe` 생성됨

### CLI로 컴파일
```bat
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" setup.iss
```

또는 PATH에 iscc가 있으면:
```bat
iscc setup.iss
```

## 3. 결과물

```
setup\Output\OrchestrationKit-Setup.exe
```

이 파일 하나만 배포하면 됨. 더블클릭하면:
- 위자드 화면 (한국어/영어 선택)
- 설치 경로 선택 (= 프로젝트 폴더)
- 컴포넌트 선택 (전체/최소/사용자지정)
- 프로그레스바 + 파일 압축 해제
- 각 모듈 자동 실행 (설정, 서비스, 도구 설치)
- 완료 후 Claude 바로 실행 옵션

## 4. 사일런트 설치 (자동화용)

```bat
OrchestrationKit-Setup.exe /SILENT /DIR="C:\work\myproject"
```

완전 무음:
```bat
OrchestrationKit-Setup.exe /VERYSILENT /DIR="C:\work\myproject" /SUPPRESSMSGBOXES
```

## 5. 배포용 bat도 함께 사용 가능

setup.exe 없이도 `setup.bat`으로 설치 가능:
```bat
cd setup
setup.bat C:\work\myproject
```
