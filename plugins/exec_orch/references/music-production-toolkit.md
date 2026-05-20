# Music Production COMMON Toolkit

> **Scope**: Music production plugin (`music_studio`) 공통 도구 카탈로그  
> **용도**: DAW, AI 작곡, MIDI, 믹싱, 배포 도구 일괄 참조  
> **업데이트**: 2026-05-20  
> **관리**: plugins/exec_orch/references/ (동기화 불필요, 참조 전용)

---

## 1. DAW (Digital Audio Workstation) & 워크스테이션

| 도구 | 플랫폼 | 설명 | 설치 |
|---|---|---|---|
| **Ableton Live** | Win/Mac | 라이브 공연 + 스튜디오 작곡. 루프 기반 | [ableton.com](https://www.ableton.com) |
| **FL Studio** | Win/Mac/Linux | 패턴 시퀀싱, MIDI 롤 우수. 초보자 친화 | [flstudio.com](https://www.flstudio.com) |
| **Logic Pro** | Mac만 | Apple 정식. 시네마틱 사운드. 고가 | [apple.com/logic-pro](https://www.apple.com/logic-pro) |
| **Reaper** | Win/Mac/Linux | 경량, 멀티트랙 강력. 저가($225) | [reaper.fm](https://www.reaper.fm) |
| **Audacity** | Win/Mac/Linux | 무료 오디오 편집기. 단순 작업 | `apt install audacity` |
| **Ardour** | Win/Mac/Linux | 오픈소스 DAW. 완전 무료 | `apt install ardour` |
| **LMMS** (Linux MultiMedia Studio) | Win/Mac/Linux | 경량 무료 DAW | `apt install lmms` |
| **GarageBand** | Mac/iPad | Apple 기본 포함. 초보자용 | MacOS 기본 포함 |
| **Studio One** | Win/Mac | Presonus 정식. 직관적 UI | [presonus.com](https://www.presonus.com) |
| **Cubase** | Win/Mac | 스타인버그 정식. 전문가 수준 | [steinberg.net/cubase](https://www.steinberg.net/cubase) |
| **Pro Tools** | Win/Mac | Avid 정식. 오디오 엔지니어 표준 | [avid.com](https://www.avid.com) |
| **Bitwig Studio** | Win/Mac/Linux | 현대적 UI, 모듈식 설계 | [bitwig.com](https://www.bitwig.com) |
| **Cakewalk by BandLab** | Win | 무료 DAW (Bandlab 인수) | [cakewalk.bandlab.com](https://www.cakewalk.bandlab.com) |
| **Adobe Audition** | Win/Mac | 오디오 편집 특화, 클라우드 동기 | `adobe.com` 구독 |
| **PreSonus Studio One Prime** | Win/Mac | Studio One 무료 버전 | [presonus.com/studio-one-prime](https://www.presonus.com/products/studio-one-prime) |

---

## 2. AI 작곡 & 생성 도구

| 도구 | 지원 포맷 | 설명 | 설치/API |
|---|---|---|---|
| **Suno AI** | MP3, WAV | 텍스트 → 전체 노래 생성 (가사+악기) | [suno.ai](https://suno.ai) (웹/API) |
| **Udio** | MP3, WAV | 스타일별 음악 생성. Suno 경쟁사 | [udio.com](https://www.udio.com) |
| **MusicGen** (Meta) | WAV | 텍스트 설명 → 음악. 오픈소스 | `pip install audiocraft` |
| **AudioCraft** | WAV | Meta 프레임워크. 음성 합성 포함 | `pip install audiocraft` |
| **Riffusion** | MP3 | 가사 + 스타일 → 음악 생성 | `pip install diffusers torch` |
| **AIVA** | MIDI, WAV | 영화/게임 사운드트랙 생성 | [aiva.ai](https://www.aiva.ai) |
| **Amper Music** | MP3 | 감정/분위기 기반 배경음악 | [ampermusic.com](https://www.ampermusic.com) |
| **Soundraw** | MP3, WAV | 재즈, 팝, EDM 등 장르별 | [soundraw.io](https://www.soundraw.io) |
| **Boomy** | MP3, WAV | 쉬운 인터페이스로 곡 제작 | [boomy.com](https://www.boomy.com) |
| **MuseNet** (OpenAI) | MIDI | 클래식/팝/재즈 생성. 백터 제어 | [openai.com/research/musenet](https://openai.com/research/musenet/) |
| **OpenAI Music (Jukebox)** | MP3 | 가사+장르 → 음성 포함 음악 | deprecated (Suno 로 전환) |
| **Google MusicLM** | WAV | 텍스트 설명으로 음악 생성 | google.ai (제한 공개) |
| **Splice Beatmaker** | MP3 | 루프 기반 비트 생성 | [splice.com](https://www.splice.com) |

---

## 3. MIDI 처리 & 음악 정보 처리 (MIR)

| 도구/라이브러리 | 언어 | 설명 | 설치 |
|---|---|---|---|
| **music21** | Python | 음악 분석, MIDI 처리, 음악 이론 | `pip install music21` |
| **pretty_midi** | Python | MIDI 읽기/쓰기, 피아노롤 시각화 | `pip install pretty_midi` |
| **mido** | Python | MIDI 파싱, 심플 API | `pip install mido` |
| **FluidSynth** | C/Binding | MIDI → WAV 렌더링. SF2 사운드폰트 | `apt install fluidsynth` |
| **Magenta (TensorFlow)** | Python | Google 음악 AI 프레임워크 | `pip install magenta` |
| **librosa** | Python | 음성 특성 추출, 스펙트로그램 | `pip install librosa` |
| **TidalCycles** | Haskell/SuperCollider | 라이브 코딩 음악. Algorave | `ghcup install` |
| **SuperCollider** | Supercollider | 사운드 합성, 서버형 | `apt install supercollider` |
| **Csound** | C-based | 실시간 음성 처리 | `apt install csound` |
| **pydub** | Python | 오디오 슬라이싱, 포맷 변환 | `pip install pydub` |
| **essentia** | C++/Python | 음악 특성 분석 (MPEG-7) | `pip install essentia-extractor` |
| **jMIR** | Java | 음악 정보 추출 | [jmir.sourceforge.net](http://jmir.sourceforge.net) |
| **OpenSMILE** | C++ | 음성/음악 특성 추출 | [audeering.com/opensmile/](https://www.audeering.com/opensmile/) |
| **melodyne** (SDK) | C++ | 피치 감지, 교정 | [celemony.com](https://www.celemony.com) |
| **harmonically** | Python | 코드 인식 (Chordify 대체) | `pip install harmonically` |

---

## 4. 믹싱, 마스터링 & EQ/컴프레서

| 도구/플러그인 | 유형 | 설명 | 가격 |
|---|---|---|---|
| **iZotope Ozone** | VST/AU | 마스터링 스위트. 리코버리, 스펙트럼 분석 | $99~$299 |
| **Waves SSL Comp** | VST/AU | 전설의 SSL 콘솔 컴프레서 | $29 |
| **FabFilter Pro-Q 3** | VST/AU | 동적 EQ, 광대역 분석 | $129 |
| **FabFilter Pro-C 2** | VST/AU | 컴프레서 + 보이스 전용 | $99 |
| **Spike Studio** | DAW Plugin | A/B 비교, 마스터링 체크 | $99 |
| **LANDR** (클라우드) | SaaS | 자동 마스터링 AI | $4~$30/month |
| **BandLab** | 웹 | 무료 온라인 믹싱 | Free |
| **Splice Sounds** | 라이브러리 | 샘플 + 마스터링 템플릿 | $7.99~$14.99/month |
| **Soothe2** | VST/AU | AI 공명음 제거 | $99 |
| **VocalRide** | VST/AU | 자동 보컬 레벨링 | $79 |
| **RX Suite** (iZotope) | Standalone | 노이즈 제거, 클릭 제거 | $199~$999 |
| **Descript Overdub** | 웹/App | 음성 복원, 노이즈 제거 | $24/month |
| **Accusonus ERA** | VST/AU | 배경음 제거, 음성 향상 | $49~$199 |
| **Nuendo** (Steinger) | DAW | 영상+음성 동기, 마스터링 | $669 |

---

## 5. 가사 & 작사 보조

| 도구/API | 플랫폼 | 설명 | 설치/가격 |
|---|---|---|---|
| **Genius API** | REST | 가사 데이터베이스, 곡 정보 검색 | `pip install lyricsgenius` |
| **Musixmatch API** | REST | 가사 API, 동기화 자막 | [developer.musixmatch.com](https://developer.musixmatch.com) |
| **LyricFind** | API | 대형 가사 라이센스 데이터베이스 | [corporate.lyricfind.com](https://corporate.lyricfind.com) |
| **RhymeZone** | API | 운율 사전, 유사음 검색 | [rhymezone.com/api](https://www.rhymezone.com/api) |
| **Hookpad** | 웹 | 화성 분석, 코드 진행 제안 | [hookpad.com](https://www.hookpad.com) |
| **ChatGPT/Claude** | API | 가사 초안 생성 (구조 + 톤) | `pip install openai anthropic` |
| **RhymeMe** | 웹 | 한글 운율 검색 | [rhymeme.me](https://www.rhymeme.me) |
| **Songwriter's Pad** | iOS/Android | 가사작곡 가이드, 코드 추천 | $3.99 |
| **BandLab Lyrics** | 웹 | BandLab 통합 가사 작성 | Free (BandLab) |

---

## 6. 샘플, 루프, 음원 라이브러리

| 도구/서비스 | 특징 | 설명 | 가격 |
|---|---|---|---|
| **Splice** | 라이브러리 + API | 샘플 + 플러그인. AI 검색 | $7.99~$14.99/month |
| **Loopcloud** | 라이브러리 + DAW Plugin | 수천만 루프, 원클릭 임포트 | $6.99~$19.99/month |
| **LANDR Samples** | 라이브러리 | LANDR 마스터링 + 샘플 번들 | 포함 (LANDR Pro) |
| **Freesound.org** | 커뮤니티 | 크리에이티브 커먼즈 샘플 | Free / Freesound+ $12/year |
| **Zapsplat** | 라이브러리 | SFX + 음악 샘플 (로열티 프리) | Free |
| **Epidemic Sound** | 스트림 | 무제한 음악 스트림 + 다운로드 | $9.99/month |
| **AudioJungle** | 마켓 | 저작권 음악 판매처 (ThemeForest 계열) | 곡당 $1~$39 |
| **Artlist.io** | 구독 | 영상/팟캐스트용 로열티 프리 음악 | $14.99/month |
| **BBC Sound Effects** | 공개 | BBC 아카이브 SFX (크리에이티브 커먼즈) | Free |
| **Freepd.com** | 라이브러리 | 무료 배경음악 (영상용) | Free |
| **Kevin MacLeod** | 아티스트 | Incompetech 음악, 크리에이티브 커먼즈 | Free (CC BY 3.0) |
| **SamplePacks.com** | 마켓 | 전문 샘플팩 판매 | $5~$50 |
| **Loopmasters** | 라이브러리 | 프로페셔널 샘플팩 | £2~£30 |
| **Xfer Serum Presets** | 플러그인 라이브러리 | Serum 신스 프리셋 (유명 프로듀서) | Free~$49 |

---

## 7. 음악 이론 & 분석 도구

| 도구 | 설명 | 설치 |
|---|---|---|
| **Hooktheory** | 코드 진행 데이터베이스, 팝송 분석 | [hooktheory.com](https://www.hooktheory.com) |
| **music21 (theory 모듈)** | 음악 이론 자동 분석 | `pip install music21` |
| **Chordify** | YouTube/Spotify → 자동 코드 감지 | [chordify.net](https://www.chordify.net) |
| **musicpy** | Python 음악 작곡 프레임워크 | `pip install musicpy` |
| **Ear Master** | 음감 훈련 소프트웨어 | [earmaster.com](https://www.earmaster.com) |
| **Moises** | AI 악기 분리 + 원곡 키변경 | [moises.ai](https://www.moises.ai) |
| **iReal Pro** | 재즈/팝 스탠다드 악보 + 자동 반주 | $19.99 |
| **Band-in-a-Box** | 자동 반주, 악기 배열 | [band-in-a-box.com](https://www.band-in-a-box.com) |
| **MuseScore** | 악보 작성 + 커뮤니티 (무료) | `apt install musescore` |
| **Finale** | 전문 악보 작성 소프트웨어 | [finalemusic.com](https://www.finalemusic.com) |

---

## 8. 음악 배포 & 퍼블리싱

| 도구 | 대상 | 설명 | 수수료 |
|---|---|---|---|
| **DistroKid** | 모든 스트리밍 | 모든 플랫폼 배포 (Spotify, Apple, YouTube) | 곡당 $2.49 또는 연 $99 |
| **TuneCore** | 모든 스트리밍 | 무제한 곡 배포 | $29.95/년 (10곡 이상) |
| **CD Baby** | 모든 스트리밍 + 물리 CD | 최장 기업, 피치 승인 높음 | 곡당 $0.49 또는 연 $39.95 |
| **Amuse** | 모든 스트리밍 | Spotify로 100% 로열티 (광고 기반) | 무료 + 광고 수익 분배 |
| **Ditto Music** | 모든 스트리밍 | UK 기반, 빠른 처리 | 곡당 £1.50~£3 또는 연 £25.99 |
| **Symphonic Distribution** | 모든 스트리밍 | DJ, 래퍼 친화적 | 곡당 €2 또는 연 €50 |
| **ReverbNation** | 모든 스트리밍 | 팬 엔지니어링 도구 포함 | 무료 + 곡당 $0.99 |
| **LANDR Distribution** | 모든 스트리밍 | LANDR 마스터링 + 배포 번들 | LANDR Pro 구독 포함 |
| **Groover** | Spotify, Apple Music | 큐레이터 피치 서비스 (배포 아님) | 곡당 $3.99~$7.99 |
| **Bandcamp** | 직판 + 스트리밍 | 아티스트 친화, 팬 후원 활성화 | 거래수수료 15% |
| **YouTube Content ID** | YouTube | 공식 채널 수익화 (신청 필수) | YouTube 30% 수수료 |

---

## 9. 저작권, 라이센싱 & 음악 출판

| 기관/도구 | 국가/지역 | 설명 | 용도 |
|---|---|---|---|
| **KOMCA** (한국음악저작권협회) | 한국 | 한국 음악 저작권 관리 | 저작권 등록, 로열티 징수 |
| **ASCAP** (미국) | 미국 | 미국 공연권 협회 | 라디오, TV, 스트리밍 로열티 |
| **BMI** | 미국 | 미국 공연권 협회 (ASCAP 경쟁) | 라디오, TV, 스트리밍 로열티 |
| **SESAC** | 미국 | 미국 공연권 협회 (3번째) | 공연권, 동기화권 |
| **PRS for Music** | 영국 | 영국 저작권 관리 | 공연권 관리 |
| **SABAM** | 벨기에 | 유럽 저작권 협회 | 공연권 관리 |
| **IFPI** | 국제 | 국제 음반 협회 (ISP 대리) | 국제 저작권 가이드 |
| **Creative Commons** | 국제 | CC 라이센스 (귀속, 비상업, 변경금지 등) | 무료 라이센싱 |
| **Copyright Alliance** | 국제 | 저작권 교육, 정책 옹호 | 교육 리소스 |
| **Splice Licensing** | 국제 | 샘플 사용 권리 명확화 | 샘플팩 라이센스 확인 |

---

## 10. 음향 및 사운드 디자인

| 도구 | 설명 | 설치 |
|---|---|---|
| **Spectrasonics Omnisphere** | 신스 플러그인, 프리셋 5000+ | VST/AU ($495) |
| **Native Instruments Komplete** | 신스, 샘플, FX 종합 | `komplete.native-instruments.com` |
| **Serum (Xfer)** | 웨이브테이블 신스, 사운드 디자인 | $189 |
| **Sylenth1** | 폴리신스, 아날로그 음색 | $99 |
| **Massive** (NI) | 신스 플러그인, 벨소리 제작 | $99 |
| **Wavetable** (Ableton) | 웨이브테이블 신스 (포함) | Ableton Live Suite |
| **Operator** (Max for Live) | 음성 합성, 루핑 | Max for Live $99 |
| **Kontakt** (NI) | 샘플링 엔진 | $99~$599 |
| **Samplitude Pro X** | 샘플링, 편집 특화 | $399 |
| **Ozone Spectral Resynthesizer** | 스펙트럼 재합성, 음성 복원 | iZotope Ozone Pro ($299) |

---

## 11. 음성 처리 & 보컬 효과

| 도구 | 설명 | 설치 |
|---|---|---|
| **Antares Auto-Tune** | 피치 교정, 효과 | VST/AU ($399) |
| **Melodyne** (Celemony) | 폴리포닉 피치 감지/교정 | $99~$199 |
| **VocalRide** | 자동 보컬 레벨링 | Waves VST ($79) |
| **VocalShaper** | 동적 EQ + 압축 (보컬 특화) | $199 |
| **Soothe2** | AI 공명음 제거 | $99 |
| **Voxengo Pristine Space** | 컨볼루션 리버브 | VST (무료) |
| **iZotope VoiceOver** | 라디오 DJ/팟캐스트 음성 | iZotope Ozone |
| **descript HQ** | 음성 스타일 전환 | SaaS ($24/month) |
| **Descript Overdub** | AI 음성 복제 | Descript Pro |

---

## 12. 온라인 작곡 & 협업 플랫폼

| 플랫폼 | 특징 | 가격 |
|---|---|---|
| **BandLab** | 무료 DAW + 협업 + 공유 | Free |
| **Soundtrap (Spotify)** | 웹 DAW, 샘플 라이브러리 포함 | Free / Premium $7.99/month |
| **Soundation** | 웹 DAW, 클라우드 저장 | Free / Premium $5.99/month |
| **Audiotool** | 브라우저 DAW, 실시간 협업 | Free |
| **Chrome Music Lab** | 구글 교육용 음악 도구 | Free (교육용) |
| **Splice Studio** | 클라우드 협업 + 버전 관리 | $7.99~/month |
| **Dropvox** | 음성 메모 협업 | Free / Pro $5/month |
| **BeatStars** | 비트 판매 마켓플레이스 | 판매 60/40 |

---

## 13. 음악 메타데이터 & 카탈로깅

| 도구 | 설명 | 설치 |
|---|---|---|
| **MusicBrainz** | 음악 메타데이터 DB (오픈소스) | [musicbrainz.org](https://musicbrainz.org) |
| **AcoustID** | 음악 핑거프린팅 (Shazam 방식) | `pip install acoustid` |
| **ISRC** | 국제 음반 표준코드 (ISO) | 음반사가 신청 |
| **Gracenote** (Nielsen) | 음악 메타데이터 (상업) | 라이센스 필요 |
| **Discogs** | 음악/영화 디스코그래피 | [discogs.com](https://www.discogs.com) |
| **All Music Guide** | 음악 리뷰 + 메타데이터 | [allmusic.com](https://www.allmusic.com) |

---

## 14. 팟캐스트 & 보컬 레코딩

| 도구 | 설명 | 설치 |
|---|---|---|
| **Descript** | 팟캐스트 편집 (음성→텍스트) | [descript.com](https://www.descript.com) $24/month |
| **Anchor** (Spotify) | 무료 팟캐스트 호스팅 | Free (Spotify) |
| **Buzzsprout** | 팟캐스트 호스팅 + 배포 | Free / Pro $12~$24/month |
| **Podbean** | 팟캐스트 호스팅 + 분석 | Free / Premium $5~$99/month |
| **Riverside.fm** | 원격 녹음 + 편집 | $15~$99/month |
| **Audition** (Adobe) | 팟캐스트 오디오 편집 | $22.49/month (Creative Cloud) |

---

## 15. 한글 음악 도구 & 서비스

| 도구 | 특징 | 링크 |
|---|---|---|
| **멜론** | 한국 최대 음악 스트리밍 | [melon.com](https://www.melon.com) |
| **지니뮤직** | LG U+ 자회사, SK텔레콤 제휴 | [genie.co.kr](https://www.genie.co.kr) |
| **벅스** | 카카오 산하 스트리밍 | [bugs.co.kr](https://www.bugs.co.kr) |
| **유튜브뮤직** | 글로벌 스트리밍 (한곡 선택) | [music.youtube.com](https://music.youtube.com) |
| **소리바다** | 국내 디지털 음악 플랫폼 | [soribada.com](https://www.soribada.com) |
| **K뮤직** | 한국 클래식·전통음악 플랫폼 | [kmusic.go.kr](https://www.kmusic.go.kr) |
| **한국음악저작권협회** | 저작권 등록 기관 | [komca.or.kr](https://www.komca.or.kr) |
| **KOCIS 한국음악** | 정부 문화 프로모션 | [kocis.go.kr](https://www.kocis.go.kr) |
| **스마트 스토어** (음악기기) | 악기/헤드폰/마이크 판매 | [smartstore.naver.com](https://smartstore.naver.com) |

---

## 참조

- **DAW 비교**: [DAW 비교표](docs/2026-05-20/daw-comparison.md) (가격, 플랫폼, 특징)
- **플러그인 안내**: [VST/AU 플러그인 설치](docs/2026-05-20/plugin-installation.md)
- **배포 가이드**: [음악 배포 체크리스트](docs/2026-05-20/music-distribution-checklist.md)
- **저작권 안내**: [KOMCA 등록 방법](docs/2026-05-20/komca-guide.md)
- **팟캐스트 안내**: [팟캐스트 제작 가이드](docs/2026-05-20/podcast-guide.md)

---

**최종 업데이트**: 2026-05-20  
**총 도구 개수**: 150+  
**유지보수**: 월별 신규 도구 추가
