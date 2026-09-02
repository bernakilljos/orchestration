# 터미널·검색 도구 룰

> **근거**: 2026-09-02 · fzf·rga·bat·eza·lazygit·git-delta 통합.

## 절대 룰

**모던 CLI 도구 활용 · Unix 기본 대체 (사용자 명시 시).**

## 도구 매트릭스

| 기존 | 모던 대체 | 이유 |
|---|---|---|
| `find` | **fzf** + `fd` | fuzzy 검색 · 인터랙티브 |
| `grep`·`rg` | **ripgrep-all (rga)** | PDF·docx·xlsx·zip 도 검색 |
| `cat` | **bat** | syntax highlighting · line number |
| `ls` | **eza** | 컬러 · git 통합 · icon |
| `cd` | **zoxide** | 자주 방문 폴더 자동 |
| `diff` | **git-delta** | 컬러 · syntax highlight |
| `git status/log` | **lazygit** | TUI · 편리 |
| `top`/`htop` | **btop / btm** | 모던 시스템 모니터 |

## 설치 (Windows)

```powershell
# scoop
scoop install fzf ripgrep bat eza zoxide delta lazygit btop

# 또는 winget
winget install junegunn.fzf BurntSushi.ripgrep sharkdp.bat eza-community.eza ajeetdsouza.zoxide dandavison.delta jesseduffield.lazygit aristocratos.btop
```

## 설치 (Mac/Linux)

```bash
# brew (Mac)
brew install fzf ripgrep bat eza zoxide git-delta lazygit btop

# apt (Ubuntu)
sudo apt install ripgrep bat fd-find
# ripgrep-all: cargo install ripgrep_all
# eza: cargo install eza
```

## 활용 예

```bash
# 파일 fuzzy 검색 + edit
fzf --preview 'bat --color=always {}' | xargs $EDITOR

# PDF 안 내용 검색
rga "개인정보" docs/

# git diff 컬러
git diff | delta

# git TUI
lazygit
```

## 우리 kit 통합

- `.claude/scripts/install-terminal-tools.sh` (예정 · sudo 없이 설치)
- shell alias 자동 등록 (setup/modules 예정)

## 관련

- `.claude/rules/language-standards.md`
- `.claude/rules/auto-optimization.md`
