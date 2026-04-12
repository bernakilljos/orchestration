; =====================================================
; Orchestration Kit - Inno Setup Script
;
; 이 파일을 Inno Setup Compiler로 컴파일하면 setup.exe 생성
; 다운로드: https://jrsoftware.org/isdl.php
;
; 컴파일: iscc setup.iss
; 결과:   Output\OrchestrationKit-Setup.exe
; =====================================================

#define MyAppName "Orchestration Kit"
#define MyAppVersion "3.0"
#define MyAppPublisher "Multi-AI Orchestration"
#define MyAppURL "https://github.com/pjt-orchestration"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppSupportURL={#MyAppURL}
DefaultDirName=C:\work\new_project
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; 압축 설정 (프로그레스바 표시됨)
Compression=lzma2/max
SolidCompression=yes
; 출력 설정
OutputDir=Output
OutputBaseFilename=OrchestrationKit-Setup
; 아이콘 (있으면 사용, 없으면 기본)
; SetupIconFile=..\icon.ico
; 관리자 권한 요청
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
; 설치 위자드 설정
WizardStyle=modern
WizardSizePercent=120
; 언인스톨러
Uninstallable=yes
UninstallDisplayName={#MyAppName}
; 디렉토리 선택 허용
AllowNoIcons=yes
DisableDirPage=no
; 라이센스/정보 페이지 (선택)
; LicenseFile=..\LICENSE
InfoBeforeFile=setup-info.rtf

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
korean.WelcomeLabel2=Multi-AI Orchestration Kit을 설치합니다.%n%nClaude + Codex + Gemini를 자동 연동하는 개발 환경을 구성합니다.%n%n설치할 프로젝트 경로를 선택하세요.
korean.FinishedLabel=설치가 완료되었습니다!%n%nClaude를 실행하면 자동으로 환경이 구성됩니다.

[Types]
Name: "full"; Description: "전체 설치 (추천)"
Name: "minimal"; Description: "최소 설치 (코어 파일만)"
Name: "custom"; Description: "사용자 지정"; Flags: iscustom

[Components]
Name: "core";        Description: ".claude 폴더 + CLAUDE.md";          Types: full minimal custom; Flags: fixed
Name: "commands";    Description: "글로벌 명령어 (codex-a, gemini-a)"; Types: full custom
Name: "services";    Description: "status-push / remote-agent 서비스"; Types: full custom
Name: "prereqs";     Description: "Node.js / Claude Code / Cloudflared"; Types: full custom
Name: "github";      Description: "Git 초기화 + GitHub 연동";          Types: full custom
Name: "plugins";     Description: "Claude 플러그인";                    Types: full custom
Name: "videorestore"; Description: "동영상 복원 (CodeFormer + Real-ESRGAN)"; Types: full custom

[Files]
; --- Core: .claude 폴더 전체 ---
Source: "..\.claude\*"; DestDir: "{app}\.claude"; Components: core; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\CLAUDE.md"; DestDir: "{app}"; Components: core; Flags: ignoreversion

; --- Docs/Templates ---
Source: "..\docs\*"; DestDir: "{app}\docs"; Components: core; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\context\*"; DestDir: "{app}\context"; Components: core; Flags: ignoreversion recursesubdirs skipifsourcedoesntexist
Source: "..\templates\*"; DestDir: "{app}\templates"; Components: core; Flags: ignoreversion recursesubdirs skipifsourcedoesntexist
Source: "..\outputs\*"; DestDir: "{app}\outputs"; Components: core; Flags: ignoreversion recursesubdirs skipifsourcedoesntexist

; --- Service scripts (project root에 있는 것들) ---
Source: "..\status-push.ps1"; DestDir: "{app}"; Components: services; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\status-push-silent.vbs"; DestDir: "{app}"; Components: services; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\remote-agent.ps1"; DestDir: "{app}"; Components: services; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\remote-agent-silent.vbs"; DestDir: "{app}"; Components: services; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\cloudflared.exe"; DestDir: "{app}"; Components: prereqs; Flags: ignoreversion skipifsourcedoesntexist

; --- Setup modules (post-install에서 사용) ---
Source: "modules\*"; DestDir: "{tmp}\setup-modules"; Flags: ignoreversion deleteafterinstall
Source: "setup.bat"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall

; --- Video Restore tools ---
Source: "..\tools\video-restore.py"; DestDir: "{app}\tools\video-restore"; Components: videorestore; Flags: ignoreversion

; --- Root scripts ---
Source: "..\codex-auto.bat"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\gemini-auto.bat"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\guide.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Dirs]
Name: "{app}\docs\adr"
Name: "{app}\docs\deploy-history"
Name: "{app}\docs\screens"
Name: "{app}\context"
Name: "{app}\templates"
Name: "{app}\outputs"
Name: "{app}\.claude\tasks"
Name: "{app}\.claude\tasks\locks"
Name: "{app}\.claude\tasks\done"
Name: "{app}\.claude\context-cache"
Name: "{app}\tools\video-restore"

[Run]
; --- Post-install: 각 모듈 실행 (프로그레스바 표시) ---
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\02-defender.bat"" ""{userappdata}\.."""; StatusMsg: "Windows Defender 예외 설정..."; Components: core; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\03-settings.bat"" ""{userappdata}\.."" ""{app}"""; StatusMsg: "Claude 설정 구성..."; Components: core; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\04-commands.bat"" ""{app}"""; StatusMsg: "글로벌 명령어 설치..."; Components: commands; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\05-services.bat"" ""{app}"" ""{app}\"" ""{userappdata}\.."""; StatusMsg: "서비스 등록..."; Components: services; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\06-prereqs.bat"""; StatusMsg: "필수 도구 설치 (Node.js, Claude Code, Cloudflared)..."; Components: prereqs; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\07-github.bat"" ""{app}"""; StatusMsg: "Git / GitHub 설정..."; Components: github; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\08-plugins.bat"" ""{app}"" ""{app}\"""; StatusMsg: "Claude 플러그인 설치..."; Components: plugins; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\10-video-restore.bat"" ""{app}"""; StatusMsg: "동영상 복원 도구 설치 (CodeFormer + Real-ESRGAN)..."; Components: videorestore; Flags: runhidden waituntilterminated

; --- 설치 완료 후 선택적 실행 ---
Filename: "{cmd}"; Parameters: "/k cd /d ""{app}"" && claude --dangerously-skip-permissions"; Description: "Claude 바로 실행"; Flags: postinstall nowait skipifsilent unchecked

[UninstallRun]
; 서비스 정리
Filename: "{cmd}"; Parameters: "/c taskkill /f /fi ""WINDOWTITLE eq remote-agent*"" >nul 2>&1"; RunOnceId: "KillRemoteAgent"; Flags: runhidden
Filename: "{cmd}"; Parameters: "/c reg delete ""HKCU\Software\Microsoft\Windows\CurrentVersion\Run"" /v ""OrchestrationStatusPush"" /f >nul 2>&1"; RunOnceId: "UnregStatusPush"; Flags: runhidden
Filename: "{cmd}"; Parameters: "/c reg delete ""HKCU\Software\Microsoft\Windows\CurrentVersion\Run"" /v ""OrchestrationRemoteAgent"" /f >nul 2>&1"; RunOnceId: "UnregRemoteAgent"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}\.claude"
Type: filesandordirs; Name: "{app}\docs"
Type: filesandordirs; Name: "{app}\context"
Type: filesandordirs; Name: "{app}\templates"
Type: filesandordirs; Name: "{app}\outputs"
Type: filesandordirs; Name: "{app}\tools"

[Code]
// =====================================================
// Pascal Script: 설치 중 .gitignore 자동 생성
// =====================================================
procedure CurStepChanged(CurStep: TSetupStep);
var
  GitIgnorePath: string;
  Content: string;
begin
  if CurStep = ssPostInstall then
  begin
    GitIgnorePath := ExpandConstant('{app}\.gitignore');
    if not FileExists(GitIgnorePath) then
    begin
      Content := '.claude/deploy-config.env' + #13#10 +
                 '.claude/context-cache/' + #13#10 +
                 '.claude/tasks/locks/' + #13#10 +
                 '.claude/orca-heartbeat' + #13#10 +
                 'docs/secret-scan.txt' + #13#10 +
                 'docs/build-result.txt' + #13#10 +
                 'node_modules/' + #13#10 +
                 '.env' + #13#10 +
                 '.env.local' + #13#10 +
                 '*.log' + #13#10;
      SaveStringToFile(GitIgnorePath, Content, False);
    end;

    // deploy-config.env 생성
    if not FileExists(ExpandConstant('{app}\.claude\deploy-config.env')) then
    begin
      if FileExists(ExpandConstant('{app}\.claude\deploy-config.env.example')) then
        CopyFile(
          ExpandConstant('{app}\.claude\deploy-config.env.example'),
          ExpandConstant('{app}\.claude\deploy-config.env'),
          False
        );
    end;

    // orca-enabled 플래그
    if not FileExists(ExpandConstant('{app}\.claude\orca-stopped')) then
    begin
      if not FileExists(ExpandConstant('{app}\.claude\orca-enabled')) then
        SaveStringToFile(ExpandConstant('{app}\.claude\orca-enabled'), 'enabled', False);
    end;
  end;
end;
