; =====================================================
; Orchestration Kit - Inno Setup Script
;
; 이 파일을 Inno Setup Compiler로 컴파일하면 setup.exe 생성
; 다운로드: https://jrsoftware.org/isdl.php
;
; 컴파일: iscc setup.iss
; 결과:   Output\OrchestrationKit-Setup.exe
;
; 위자드 첫 화면에서 3가지 모드 선택 (라디오 버튼):
;   ⦿ Full Orchestration (Claude+Codex+Gemini)
;   ○ Codex 단독 (Claude 없이)
;   ○ Gemini 단독 (Claude 없이)
;   ○ 사용자 지정
; =====================================================

#define MyAppName "Orchestration Kit"
#define MyAppVersion "1.0"
#define MyAppPublisher "Multi-AI Orchestration"
#define MyAppURL "https://github.com/bernakilljos/orchestration"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppSupportURL={#MyAppURL}
; setup.exe 의 부모의 부모 폴더 = orchestration_v1 또는 orchestration_v1_team
; (setup.exe 위치: {src}\setup\Output\setup.exe → {src}\..\.. 가 본체)
DefaultDirName={src}\..\..
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
Compression=lzma2/max
SolidCompression=yes
OutputDir=Output
OutputBaseFilename=OrchestrationKit-Setup
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern
WizardSizePercent=120
Uninstallable=yes
UninstallDisplayName={#MyAppName}
AllowNoIcons=yes
DisableDirPage=no
InfoBeforeFile=setup-info.rtf

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
korean.WelcomeLabel2=Multi-AI Orchestration Kit을 설치합니다.%n%n다음 화면에서 모드를 선택하세요:%n%n  · Full Orchestration — Claude + Codex + Gemini 풀 연동%n  · Codex 단독 — Claude 없이 Codex 만 사용%n  · Gemini 단독 — Claude 없이 Gemini 만 사용%n%n설치할 프로젝트 경로를 선택하세요.
korean.SelectComponentsLabel2=원하는 모드를 라디오 버튼으로 선택하세요. 컴포넌트는 자동으로 맞춰집니다.
korean.FinishedLabel=설치가 완료되었습니다!%n%n사용법은 guide.txt 참조.

[Types]
Name: "full_orch";  Description: "Full Orchestration — Claude + Codex + Gemini (추천)"
Name: "codex_only"; Description: "Codex 단독 — Claude 없이"
Name: "gemini_only"; Description: "Gemini 단독 — Claude 없이"
Name: "custom";     Description: "사용자 지정"; Flags: iscustom

[Components]
; --- 공통 (모든 모드) ---
Name: "core_common";  Description: "공통 — 폴더 구조 + docs/guide.txt"; Types: full_orch codex_only gemini_only custom; Flags: fixed

; --- Claude 오케스트레이션 (full_orch 만) ---
Name: "claude_orch";  Description: "Claude 오케스트레이션 (.claude/, plugins/, CLAUDE.md)"; Types: full_orch custom

; --- Codex 환경 ---
Name: "codex_env";    Description: "Codex 환경 (AGENTS.md, .codex/, install_codex.bat)"; Types: full_orch codex_only custom

; --- Gemini 환경 ---
Name: "gemini_env";   Description: "Gemini 환경 (GEMINI.md, .gemini/, install_gemini.bat)"; Types: full_orch gemini_only custom

; --- 보조 ---
Name: "commands";     Description: "글로벌 명령어 (codex-a, gemini-a)"; Types: full_orch codex_only gemini_only custom
Name: "services";     Description: "status-push / remote-agent (Claude 전용)"; Types: full_orch custom
Name: "prereqs";      Description: "Node.js / Claude Code / Cloudflared"; Types: full_orch codex_only gemini_only custom
Name: "github";       Description: "Git 초기화 + GitHub 연동"; Types: full_orch custom
Name: "plugins";      Description: "Claude 플러그인 (Claude 전용)"; Types: full_orch custom
Name: "mediaenhance"; Description: "미디어 의존성 (오디오/PDF/PPT)"; Types: full_orch custom

[Files]
; --- Common: docs / templates / outputs / guide ---
Source: "..\docs\*";      DestDir: "{app}\docs";      Components: core_common; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\templates\*"; DestDir: "{app}\templates"; Components: core_common; Flags: ignoreversion recursesubdirs skipifsourcedoesntexist
Source: "..\outputs\*";   DestDir: "{app}\outputs";   Components: core_common; Flags: ignoreversion recursesubdirs skipifsourcedoesntexist
Source: "..\guide.txt";   DestDir: "{app}";           Components: core_common; Flags: ignoreversion skipifsourcedoesntexist

; --- Claude 오케스트레이션 ---
Source: "..\.claude\*";        DestDir: "{app}\.claude";        Components: claude_orch; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\CLAUDE.md";        DestDir: "{app}";                Components: claude_orch; Flags: ignoreversion
Source: "..\.claude-plugin\*"; DestDir: "{app}\.claude-plugin"; Components: claude_orch; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\plugins\*";        DestDir: "{app}\plugins";        Components: claude_orch; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\context\*";        DestDir: "{app}\context";        Components: claude_orch; Flags: ignoreversion recursesubdirs skipifsourcedoesntexist

; --- Codex 환경 ---
Source: "..\AGENTS.md";          DestDir: "{app}";       Components: codex_env; Flags: ignoreversion
Source: "..\.codex\*";           DestDir: "{app}\.codex"; Components: codex_env; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\install_codex.bat";  DestDir: "{app}";       Components: codex_env; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\codex-auto.bat";     DestDir: "{app}";       Components: codex_env; Flags: ignoreversion skipifsourcedoesntexist

; --- Gemini 환경 ---
Source: "..\GEMINI.md";          DestDir: "{app}";        Components: gemini_env; Flags: ignoreversion
Source: "..\.gemini\*";          DestDir: "{app}\.gemini"; Components: gemini_env; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\install_gemini.bat"; DestDir: "{app}";        Components: gemini_env; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\gemini-auto.bat";    DestDir: "{app}";        Components: gemini_env; Flags: ignoreversion skipifsourcedoesntexist

; --- 보조 ---
Source: "..\status-push.ps1";        DestDir: "{app}"; Components: services; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\status-push-silent.vbs"; DestDir: "{app}"; Components: services; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\remote-agent.ps1";       DestDir: "{app}"; Components: services; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\remote-agent-silent.vbs"; DestDir: "{app}"; Components: services; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\cloudflared.exe";        DestDir: "{app}"; Components: prereqs;  Flags: ignoreversion skipifsourcedoesntexist

; --- Setup 모듈 (post-install용 임시) ---
Source: "modules\*"; DestDir: "{tmp}\setup-modules"; Flags: ignoreversion deleteafterinstall
Source: "setup.bat"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall

[Dirs]
Name: "{app}\docs\adr"
Name: "{app}\docs\deploy-history"
Name: "{app}\docs\screens"
Name: "{app}\templates"
Name: "{app}\outputs"
; Claude 모드 전용
Name: "{app}\context";                Components: claude_orch
Name: "{app}\.claude\tasks";          Components: claude_orch
Name: "{app}\.claude\tasks\locks";    Components: claude_orch
Name: "{app}\.claude\tasks\done";     Components: claude_orch
Name: "{app}\.claude\context-cache";  Components: claude_orch
Name: "{app}\tools\media-enhance";    Components: mediaenhance
Name: "{app}\tools\media-enhance\enhancers"; Components: mediaenhance
Name: "{app}\tools\media-enhance\utils";     Components: mediaenhance
; Codex / Gemini standalone 모드 전용
Name: "{app}\tasks";       Components: codex_env or gemini_env
Name: "{app}\tasks\done";  Components: codex_env or gemini_env

[Run]
; --- Claude 오케스트레이션 모듈 (claude_orch 선택 시) ---
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\02-defender.bat"" ""{userappdata}\.."""; StatusMsg: "Windows Defender 예외 설정..."; Components: claude_orch; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\03-settings.bat"" ""{userappdata}\.."" ""{app}"""; StatusMsg: "Claude 설정 구성..."; Components: claude_orch; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\04-commands.bat"" ""{app}"""; StatusMsg: "글로벌 명령어 설치..."; Components: commands; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\05-services.bat"" ""{app}"" ""{app}\"" ""{userappdata}\.."""; StatusMsg: "서비스 등록..."; Components: services; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\06-prereqs.bat"""; StatusMsg: "필수 도구 설치 (Node.js, Claude Code, Cloudflared)..."; Components: prereqs; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\07-github.bat"" ""{app}"""; StatusMsg: "Git / GitHub 설정..."; Components: github; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\08-plugins.bat"" ""{app}"" ""{app}\"""; StatusMsg: "Claude 플러그인 설치..."; Components: plugins; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\11-media-enhance.bat"" ""{app}"""; StatusMsg: "미디어 의존성 설치..."; Components: mediaenhance; Flags: runhidden waituntilterminated
Filename: "{cmd}"; Parameters: "/c ""{tmp}\setup-modules\14-mcp-figma.bat"""; StatusMsg: "ClaudeTalkToFigma MCP 등록..."; Components: claude_orch; Flags: runhidden waituntilterminated

; --- Codex standalone (codex_env 선택 + claude_orch 미선택 시) ---
Filename: "{cmd}"; Parameters: "/c ""{app}\install_codex.bat"" ""{app}"""; StatusMsg: "Codex Standalone 환경 구성..."; Components: codex_env; Check: NotClaudeOrch; Flags: runhidden waituntilterminated

; --- Gemini standalone (gemini_env 선택 + claude_orch 미선택 시) ---
Filename: "{cmd}"; Parameters: "/c ""{app}\install_gemini.bat"" ""{app}"""; StatusMsg: "Gemini Standalone 환경 구성..."; Components: gemini_env; Check: NotClaudeOrch; Flags: runhidden waituntilterminated

; --- 설치 완료 후 선택적 실행 ---
Filename: "{cmd}"; Parameters: "/k cd /d ""{app}"" && claude --dangerously-skip-permissions"; Description: "Claude 바로 실행"; Components: claude_orch; Flags: postinstall nowait skipifsilent unchecked
Filename: "{cmd}"; Parameters: "/k cd /d ""{app}"" && codex-go"; Description: "Codex 대화 모드 시작"; Components: codex_env; Check: NotClaudeOrch; Flags: postinstall nowait skipifsilent unchecked
Filename: "{cmd}"; Parameters: "/k cd /d ""{app}"" && gemini-go"; Description: "Gemini 대화 모드 시작"; Components: gemini_env; Check: NotClaudeOrch; Flags: postinstall nowait skipifsilent unchecked

[UninstallRun]
Filename: "{cmd}"; Parameters: "/c taskkill /f /fi ""WINDOWTITLE eq remote-agent*"" >nul 2>&1"; RunOnceId: "KillRemoteAgent"; Flags: runhidden
Filename: "{cmd}"; Parameters: "/c reg delete ""HKCU\Software\Microsoft\Windows\CurrentVersion\Run"" /v ""OrchestrationStatusPush"" /f >nul 2>&1"; RunOnceId: "UnregStatusPush"; Flags: runhidden
Filename: "{cmd}"; Parameters: "/c reg delete ""HKCU\Software\Microsoft\Windows\CurrentVersion\Run"" /v ""OrchestrationRemoteAgent"" /f >nul 2>&1"; RunOnceId: "UnregRemoteAgent"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}\.claude"
Type: filesandordirs; Name: "{app}\.codex"
Type: filesandordirs; Name: "{app}\.gemini"
Type: filesandordirs; Name: "{app}\docs"
Type: filesandordirs; Name: "{app}\context"
Type: filesandordirs; Name: "{app}\templates"
Type: filesandordirs; Name: "{app}\outputs"
Type: filesandordirs; Name: "{app}\tasks"
Type: filesandordirs; Name: "{app}\tools"

[Code]
// =====================================================
// Pascal Script
// =====================================================

// GitHub PAT 입력 페이지 (마법사 안에서 PAT 받기)
var
  PatPage: TInputQueryWizardPage;

procedure InitializeWizard();
begin
  PatPage := CreateInputQueryPage(wpSelectComponents,
    'GitHub Personal Access Token',
    'GitHub 자동 push / repo 생성을 위해 PAT 가 필요합니다.',
    '비워두면 SKIP — 설치는 진행되며 GitHub 자동 기능만 비활성됩니다.' + #13#10 +
    'PAT 발급: https://github.com/settings/tokens (scope: repo + workflow)');
  PatPage.Add('GitHub PAT (ghp_... 형식, 비우면 SKIP):', False);
end;

// codex/gemini standalone 모드 — Claude orchestration 미선택일 때만 install_*.bat 실행
function NotClaudeOrch: Boolean;
begin
  Result := not WizardIsComponentSelected('claude_orch');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  GitIgnorePath: string;
  Content: string;
  IniPath: string;
  IniDir: string;
  PatValue: string;
begin
  if CurStep = ssInstall then
  begin
    // PAT 입력값을 docs/ini/github.ini 에 저장 (install/setup 흐름이 읽음)
    PatValue := PatPage.Values[0];
    if PatValue <> '' then
    begin
      IniDir := ExpandConstant('{app}\docs\ini');
      IniPath := IniDir + '\github.ini';
      ForceDirectories(IniDir);
      Content := '# GitHub PAT (Inno Setup 마법사 입력 — ' + GetDateTimeString('yyyy-mm-dd hh:nn:ss', '-', ':') + ')' + #13#10 +
                 '# 절대 git commit 금지 (.gitignore 됨)' + #13#10 +
                 'GITHUB_PAT=' + PatValue + #13#10;
      SaveStringToFile(IniPath, Content, False);
    end;
  end;

  if CurStep = ssPostInstall then
  begin
    // 모든 모드에서 .gitignore 생성
    GitIgnorePath := ExpandConstant('{app}\.gitignore');
    if not FileExists(GitIgnorePath) then
    begin
      Content := '.claude/deploy-config.env' + #13#10 +
                 '.claude/context-cache/' + #13#10 +
                 '.claude/tasks/locks/' + #13#10 +
                 '.claude/tasks/done/' + #13#10 +
                 '.claude/orca-heartbeat' + #13#10 +
                 '.claude/orca-enabled' + #13#10 +
                 '.claude/state/' + #13#10 +
                 'tasks/done/' + #13#10 +
                 'docs/secret-scan.txt' + #13#10 +
                 'docs/build-result.txt' + #13#10 +
                 'install-test-*.txt' + #13#10 +
                 'node_modules/' + #13#10 +
                 '.env' + #13#10 +
                 '.env.local' + #13#10 +
                 '*.log' + #13#10;
      SaveStringToFile(GitIgnorePath, Content, False);
    end;

    // Claude 모드 전용 파일들
    if WizardIsComponentSelected('claude_orch') then
    begin
      // deploy-config.env
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
end;
