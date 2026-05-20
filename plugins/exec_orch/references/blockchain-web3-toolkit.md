# Blockchain & Web3 Toolkit Reference

> **목적**: 블록체인·Web3 전체 생태계의 공통 도구 카탈로그 (domain-agnostic)
> **대상**: 모든 블록체인·DeFi·NFT·DAO 플러그인·스킬에서 참고
> **최종 갱신**: 2026-05-20

---

## 📊 카테고리 요약

| # | 카테고리 | 도구 수 | 핵심 용도 |
|----|---------|--------|---------|
| 1 | 🔐 스마트 컨트랙트 언어 | 8 | Solidity, Vyper, Rust, Move, Cairo, 컴파일 |
| 2 | 🛠️ 개발 프레임워크 | 12 | Hardhat, Foundry, Truffle, Brownie, Anchor, 테스트 |
| 3 | 💻 JS/TS 라이브러리 | 15 | ethers.js, viem, web3.js, wagmi, RainbowKit |
| 4 | 🐍 Python 라이브러리 | 10 | web3.py, Brownie, Ape, 상호작용 |
| 5 | 👛 지갑 & 인증 | 12 | MetaMask, Phantom, WalletConnect, Safe |
| 6 | 🌐 노드 & RPC | 15 | Infura, Alchemy, QuickNode, Ankr, 로컬 노드 |
| 7 | 🔍 블록 탐색기 & 인덱싱 | 10 | Etherscan, The Graph, Dune, Nansen |
| 8 | 💰 DeFi 도구 & SDK | 12 | Uniswap, 1inch, Aave, Curve, Chainlink |
| 9 | 🖼️ NFT & 토큰 | 10 | OpenSea API, Metaplex, Zora, thirdweb |
| 10 | 🗂️ IPFS & 탈중앙 스토리지 | 10 | IPFS, Pinata, Arweave, Filecoin, Ceramic |
| 11 | 🔒 보안 감사 & 분석 | 12 | Slither, Mythril, Certora, Trail of Bits |
| 12 | ⛓️ L2 & 스케일링 | 8 | Optimism, Arbitrum, zkSync, Polygon, Base |
| 13 | 🌉 크로스체인 & 브릿지 | 8 | LayerZero, Wormhole, Axelar, Hyperlane |
| 14 | 📊 데이터 & 분석 | 8 | Dune, Flipside, Covalent, GraphQL 도구 |
| 15 | 🏛️ DAO & 거버넌스 | 10 | Snapshot, Tally, Aragon, Governor, Colony |

**총 도구 수: 140개** (각 카테고리별 최소 8개 이상)

---

## 1️⃣ 스마트 컨트랙트 언어 (Smart Contract Languages)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 1.1 | Solidity | Ethereum 및 EVM 호환 네트워크의 주요 언어 | `npm install -g solc` |
| 1.2 | Vyper | Python 유사 문법의 EVM 계약 언어 — 보안 강화 | `pip install vyper` |
| 1.3 | Rust (Solana) | Solana 기반 고성능 컨트랙트 개발 언어 | `rustup default stable` |
| 1.4 | Move (Aptos/Sui) | 선형 타입 기반 안전성 강조 언어 | `brew install move` |
| 1.5 | Cairo (StarkNet) | zk-SNARK 증명 최적화 언어 | `pip install cairo-lang` |
| 1.6 | Teal (Algorand) | Algorand 체인용 저수준 언어 | npm 패키지 `algorand-builder` |
| 1.7 | Go (Cosmos) | Cosmos SDK 기반 블록체인 개발 | `go install cosmossdk.io/cmd/cosmovisor@latest` |
| 1.8 | Ink! (Polkadot) | Rust 기반 Substrate 계약 언어 | `cargo install cargo-contract` |

---

## 2️⃣ 개발 프레임워크 (Development Frameworks)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 2.1 | Hardhat | Ethereum 개발 환경 — 확장성 높은 테스트·배포 | `npm install --save-dev hardhat` |
| 2.2 | Foundry | Rust 기반 고속 Solidity 테스트 & 배포 도구 | `curl -L https://foundry.paradigm.xyz \| bash` |
| 2.3 | Truffle | 가장 오래된 Solidity 개발 프레임워크 | `npm install -g truffle` |
| 2.4 | Brownie | Python 기반 EVM 개발 프레임워크 | `pip install eth-brownie` |
| 2.5 | Anchor (Solana) | Solana 프로그램 개발 프레임워크 | `npm install -g @coral-xyz/anchor` |
| 2.6 | Ape | Python 기반 스마트 컨트랙트 프레임워크 | `pip install eth-ape` |
| 2.7 | Waffle | 컴팩트한 Solidity 테스트 프레임워크 | `npm install --save-dev ethereum-waffle` |
| 2.8 | Hardhat Ignition | 선언적 배포 언어 및 모듈 | `npm install --save-dev @nomicfoundation/hardhat-ignition` |
| 2.9 | OpenZeppelin Hardhat Upgrades | 프록시 패턴 배포 및 업그레이드 | `npm install --save-dev @openzeppelin/hardhat-upgrades` |
| 2.10 | Slang (Linea) | Linea 체인용 컨트랙트 프레임워크 | `npm install -g @slang-lang/compiler` |
| 2.11 | dapptools | 고급 Solidity 테스트 및 배포 | `nix-shell -p dapp` |
| 2.12 | Mythril (분석 도구) | 스마트 컨트랙트 버그 감지 도구 | `pip install mythril` |

---

## 3️⃣ JS/TypeScript 라이브러리 (JavaScript & TypeScript Libraries)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 3.1 | ethers.js | 경량 EVM 상호작용 라이브러리 — 가장 인기 | `npm install ethers` |
| 3.2 | viem | TypeScript 중심 고성능 Ethereum 클라이언트 | `npm install viem` |
| 3.3 | web3.js | 웹소켓 기반 Ethereum 상호작용 라이브러리 | `npm install web3` |
| 3.4 | wagmi | React hooks 기반 Web3 라이브러리 | `npm install wagmi viem @tanstack/react-query` |
| 3.5 | RainbowKit | 다중 지갑 연결 UI 컴포넌트 라이브러리 | `npm install @rainbow-me/rainbowkit` |
| 3.6 | ConnectKit | Coinbase 지갑 통합 라이브러리 | `npm install connectkit` |
| 3.7 | Web3Modal | WalletConnect 기반 다중 지갑 모달 | `npm install @web3modal/ethers` |
| 3.8 | thirdweb SDK | NFT·토큰·마켓플레이스 통합 SDK | `npm install @thirdweb-dev/sdk` |
| 3.9 | Solana Web3.js | Solana 블록체인 상호작용 라이브러리 | `npm install @solana/web3.js` |
| 3.10 | Aptos TypeScript SDK | Aptos 블록체인 상호작용 라이브러리 | `npm install aptos` |
| 3.11 | @near-js/wallet-selector | NEAR Protocol 다중 지갑 선택기 | `npm install @near-wallet-selector/core` |
| 3.12 | cosmjs | Cosmos 체인 상호작용 라이브러리 | `npm install cosmjs` |
| 3.13 | sei-js | Sei Protocol 상호작용 라이브러리 | `npm install sei-js` |
| 3.14 | anchor-ts | Anchor 프레임워크 TypeScript SDK | `npm install @coral-xyz/anchor` |
| 3.15 | Uniswap V4 Hooks SDK | Uniswap V4 커스텀 훅 개발 | `npm install @uniswap/v4-core` |

---

## 4️⃣ Python 라이브러리 (Python Libraries)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 4.1 | web3.py | Python Ethereum 상호작용 라이브러리 | `pip install web3` |
| 4.2 | eth-brownie | Solidity 개발 프레임워크 (Python 기반) | `pip install eth-brownie` |
| 4.3 | eth-ape | Pythonic EVM 개발 환경 | `pip install eth-ape` |
| 4.4 | py-solc-x | Solidity 컴파일러 Python 인터페이스 | `pip install py-solc-x` |
| 4.5 | scapy-web3 | Web3 패킷 분석 및 조작 | `pip install scapy-web3` |
| 4.6 | vyper | Vyper 스마트 컨트랙트 컴파일러 | `pip install vyper` |
| 4.7 | slither | Solidity 정적 분석 보안 도구 | `pip install slither-analyzer` |
| 4.8 | manticore | 기호 실행 기반 스마트 컨트랙트 분석 | `pip install manticore` |
| 4.9 | eth-keys | 이더리움 키 암호화 유틸리티 | `pip install eth-keys` |
| 4.10 | eth-account | 이더리움 계정 관리 라이브러리 | `pip install eth-account` |

---

## 5️⃣ 지갑 & 인증 (Wallets & Authentication)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 5.1 | MetaMask | Ethereum 브라우저 확장 지갑 (가장 대중적) | https://metamask.io |
| 5.2 | Phantom | Solana/Ethereum 다중 체인 지갑 | https://phantom.app |
| 5.3 | WalletConnect | QR 기반 지갑 연결 프로토콜 2.0 | `npm install @walletconnect/web3modal` |
| 5.4 | Safe (Gnosis Safe) | 다중 서명 스마트 계약 지갑 | https://safe.global |
| 5.5 | Ledger Hardware Wallet | 오프라인 하드웨어 지갑 | https://ledger.com |
| 5.6 | Trezor Hardware Wallet | 오픈소스 하드웨어 지갑 | https://trezor.io |
| 5.7 | Coinbase Wallet | Coinbase 운영 지갑 | https://wallet.coinbase.com |
| 5.8 | Trust Wallet | 다중 토큰·체인 지원 모바일 지갑 | https://trustwallet.com |
| 5.9 | Argent | 스마트 계약 기반 지갑 (가디언 기능) | https://www.argent.xyz |
| 5.10 | Rainbow | iOS/Android 모바일 지갑 | https://rainbow.me |
| 5.11 | Magic (Fortmatic) | 이메일 기반 지갑 복구 | `npm install magic-sdk` |
| 5.12 | Web3Auth | 소셜 로그인 기반 Web3 인증 | `npm install @web3auth/web3auth` |

---

## 6️⃣ 노드 & RPC (Nodes & RPC Providers)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 6.1 | Infura | EVM 체인 RPC 엔드포인트 제공자 | https://infura.io |
| 6.2 | Alchemy | 고급 API 및 모니터링 기능 | https://www.alchemy.com |
| 6.3 | QuickNode | 빠른 RPC 및 API 인프라 | https://www.quicknode.com |
| 6.4 | Ankr | 분산 노드 제공 및 스테이킹 | https://www.ankr.com |
| 6.5 | GetBlock | 다중 체인 RPC 제공자 | https://getblock.io |
| 6.6 | Geth (Go Ethereum) | 로컬 이더리움 노드 구현 | `brew install geth` |
| 6.7 | Hardhat Network | Hardhat 내장 로컬 EVM 노드 | `npx hardhat node` |
| 6.8 | Ganache | Truffle 스위트 로컬 블록체인 | `npm install -g ganache` |
| 6.9 | Anvil (Foundry) | Foundry의 로컬 EVM 시뮬레이터 | `forge install` (Foundry 포함) |
| 6.10 | Solana Validator | Solana 로컬 노드 | `npm install -g @solana/web3.js` |
| 6.11 | Erigon | Go 기반 경량 이더리움 클라이언트 | https://github.com/ledgerwatch/erigon |
| 6.12 | Nethermind | .NET 기반 이더리움 노드 | https://github.com/NethermindEth/nethermind |
| 6.13 | OpenEthereum (Parity) | Rust 기반 이더리움 클라이언트 (유지보수 종료) | `brew install openethereum` |
| 6.14 | Prysm | Ethereum 2.0 Beacon Chain 클라이언트 | https://docs.prylabs.network |
| 6.15 | Lodestar | TypeScript Ethereum 2.0 클라이언트 | `npm install @chainsafe/lodestar` |

---

## 7️⃣ 블록 탐색기 & 인덱싱 (Block Explorers & Indexing)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 7.1 | Etherscan | Ethereum 공식 블록 탐색기 | https://etherscan.io |
| 7.2 | Polygonscan | Polygon 블록 탐색기 | https://polygonscan.com |
| 7.3 | BscScan | Binance Smart Chain 탐색기 | https://bscscan.com |
| 7.4 | Solscan | Solana 블록 탐색기 | https://solscan.io |
| 7.5 | Aptoscan | Aptos 블록 탐색기 | https://aptoscan.in |
| 7.6 | Blockscout | 오픈소스 블록 탐색기 플랫폼 | `docker run -d blockscout` |
| 7.7 | The Graph | GraphQL 기반 블록체인 인덱싱 | `npm install @graphprotocol/graph-cli` |
| 7.8 | Dune Analytics | SQL 기반 블록체인 데이터 분석 | https://dune.com |
| 7.9 | Nansen | AI 기반 온체인 데이터 분석 | https://www.nansen.ai |
| 7.10 | DefiLlama | DeFi 프로토콜 데이터 대시보드 | https://defillama.com |

---

## 8️⃣ DeFi 도구 & SDK (DeFi Tools & SDKs)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 8.1 | Uniswap SDK | Uniswap V3/V4 교환 프로토콜 | `npm install @uniswap/sdk-core @uniswap/v3-sdk` |
| 8.2 | 1inch API | DEX 어그리게이터 라우팅 API | `npm install 1inch-api` |
| 8.3 | Aave SDK | Aave 대출 프로토콜 SDK | `npm install @aave/contract-helpers` |
| 8.4 | Curve Finance API | Curve 스테이블 스왑 API | `npm install @curvefi/sdk` |
| 8.5 | Chainlink VRF | 검증 가능한 난수 생성 오라클 | `npm install @chainlink/contracts` |
| 8.6 | Chainlink Price Feeds | 가격 피드 오라클 | `npm install @chainlink/contracts` |
| 8.7 | Balancer SDK | Balancer 유동성 풀 상호작용 | `npm install @balancer-labs/sdk` |
| 8.8 | MakerDAO SDK | MakerDAO 담보화 채무 포지션 | `npm install @makerdao/dai-plugin-mcd` |
| 8.9 | Yearn SDK | Yearn 수익 최적화 프로토콜 | `npm install @yearn-finance/web-lib` |
| 8.10 | GMX API | GMX 파생상품 거래 API | `npm install @gmx-io/gmx-sdk` |
| 8.11 | Lido SDK | Liquid staking 프로토콜 | `npm install @lido-sdk/react` |
| 8.12 | Synthetix SDK | Synthetix 합성 자산 프로토콜 | `npm install @synthetixio/contracts-interface` |

---

## 9️⃣ NFT & 토큰 (NFT & Token Tools)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 9.1 | OpenSea API | NFT 마켓플레이스 API | https://docs.opensea.io |
| 9.2 | Metaplex | Solana NFT 프로토콜 | `npm install @metaplex-foundation/js` |
| 9.3 | Zora Protocol | 분산 NFT 발행 프로토콜 | `npm install @zoralabs/zora-protocol` |
| 9.4 | thirdweb NFT | NFT 배포 및 마켓플레이스 | `npm install @thirdweb-dev/contracts` |
| 9.5 | Magic Eden API | Solana NFT 마켓플레이스 API | https://magiceden.io/creators |
| 9.6 | IPFS NFT Storage | Pinata 기반 NFT 메타데이터 저장 | `npm install nft.storage` |
| 9.7 | ERC721A | 가스 최적화된 ERC721 구현 | `npm install erc721a` |
| 9.8 | ERC1155 (OpenZeppelin) | 멀티 토큰 표준 구현 | `npm install @openzeppelin/contracts` |
| 9.9 | OpenZeppelin Contracts | 표준 토큰 및 NFT 구현 라이브러리 | `npm install @openzeppelin/contracts` |
| 9.10 | Token URI Resolver | NFT 메타데이터 해석 도구 | `npm install @metaplex-foundation/mpl-core` |

---

## 🔟 IPFS & 탈중앙 스토리지 (IPFS & Decentralized Storage)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 10.1 | IPFS (InterPlanetary FS) | P2P 분산 파일 시스템 | `brew install ipfs` |
| 10.2 | Pinata | IPFS 고정 및 관리 서비스 | https://www.pinata.cloud |
| 10.3 | Arweave | 영구 데이터 저장소 블록체인 | https://www.arweave.org |
| 10.4 | Filecoin | IPFS 기반 보상형 저장소 | `npm install @web3-storage/w3up-client` |
| 10.5 | Ceramic | 분산 데이터 네트워크 | `npm install @ceramicnetwork/core` |
| 10.6 | Infura IPFS | Infura IPFS 게이트웨이 | https://infura.io/product/ipfs |
| 10.7 | Web3.Storage | Filecoin/IPFS 통합 저장소 | `npm install @web3-storage/w3cli` |
| 10.8 | Skynet (Sia) | 스카이넷 분산 저장소 | https://siasky.net |
| 10.9 | Swarm (Ethereum) | 이더리움 스워름 분산 스토리지 | `brew install swarm` |
| 10.10 | Lighthouse.Storage | 자동화된 IPFS 백업 | https://lighthouse.storage |

---

## 1️⃣1️⃣ 보안 감시 & 분석 (Security Auditing & Analysis)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 11.1 | Slither | Solidity 정적 분석 보안 도구 | `pip install slither-analyzer` |
| 11.2 | Mythril | 기호 실행 기반 버그 감지 | `pip install mythril` |
| 11.3 | Certora | 형식 검증 도구 (CVL 언어) | https://www.certora.com |
| 11.4 | Echidna | 속성 기반 퍼징 테스트 도구 | `docker run -it echidna/echidna` |
| 11.5 | Manticore | 기호 실행 버그 분석 | `pip install manticore` |
| 11.6 | Oyente | 이더리움 컨트랙트 보안 분석 | `docker pull oyente` |
| 11.7 | Securify | Securify 2.0 정적 분석 | https://github.com/eth-sri/securify2 |
| 11.8 | OpenZeppelin Audit Library | 감사 보고서 및 가이드 | https://docs.openzeppelin.com |
| 11.9 | Trail of Bits | 보안 감사 및 컨설팅 서비스 | https://www.trailofbits.com |
| 11.10 | ConsenSys Diligence | DiligenceQA 보안 도구 | https://consensys.net/diligence |
| 11.11 | Immunefi | 버그 바운티 플랫폼 | https://immunefi.com |
| 11.12 | Least Authority | 보안 감사 회사 | https://leastauthority.com |

---

## 1️⃣2️⃣ L2 & 스케일링 솔루션 (Layer 2 & Scaling Solutions)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 12.1 | Optimism SDK | Optimistic Rollup L2 솔루션 | `npm install @eth-optimism/sdk` |
| 12.2 | Arbitrum SDK | Arbitrum Nitro L2 솔루션 | `npm install @arbitrum/sdk` |
| 12.3 | zkSync SDK | zkSync Era zk-Rollup 솔루션 | `npm install zksync-web3` |
| 12.4 | StarkNet | Cairo 기반 zk-STARK L2 | `npm install starknet` |
| 12.5 | Polygon (Matic) | Plasma + Commit 체인 L2 | `npm install @maticnetwork/maticjs` |
| 12.6 | Polygon zkEVM | Polygon의 zk-Rollup 솔루션 | https://polygon.technology/polygon-zkevm |
| 12.7 | Base | Coinbase Optimism L2 | https://base.org |
| 12.8 | Scroll | Ethereum-native zk-Rollup | `npm install @scroll-tech/contracts` |

---

## 1️⃣3️⃣ 크로스체인 & 브릿지 (Cross-Chain & Bridges)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 13.1 | LayerZero | 모듈식 크로스체인 메시징 | `npm install @layerzerolabs/core` |
| 13.2 | Wormhole | 다중 체인 통신 프로토콜 | `npm install @certusone/wormhole-sdk` |
| 13.3 | Axelar | 크로스체인 일반화 메시징 | `npm install @axelar-network/axelarjs-sdk` |
| 13.4 | Hyperlane | 크로스체인 보안 통신 | `npm install @hyperlane-xyz/core` |
| 13.5 | Stargate Finance | 유동성 풀 기반 크로스체인 스왑 | `npm install @stargateprotocol/stargate-sdk` |
| 13.6 | Polygon Bridge | Polygon <-> Ethereum 브릿지 | `npm install @maticnetwork/maticjs` |
| 13.7 | Across Protocol | 유동성 기반 크로스체인 브릿지 | `npm install @across-protocol/sdk` |
| 13.8 | Symbiosis | AMM 기반 크로스체인 스왑 | https://symbiosis.finance |

---

## 1️⃣4️⃣ 데이터 & 분석 (Data & Analytics)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 14.1 | Dune Analytics | SQL 기반 온체인 분석 플랫폼 | https://dune.com |
| 14.2 | Flipside Crypto | 크립토 데이터 분석 플랫폼 | https://www.flipsidecrypto.com |
| 14.3 | Covalent API | 범용 블록체인 API | `npm install @covalenthq/client-sdk` |
| 14.4 | DefiLlama API | DeFi 데이터 API | `curl https://api.defillama.com/` |
| 14.5 | Nansen | AI 기반 온체인 분석 | https://www.nansen.ai |
| 14.6 | Etherscan API | Etherscan 블록 데이터 API | `npm install etherscan-api` |
| 14.7 | SolanaFM | Solana 트랜잭션 분석기 | https://solana.fm |
| 14.8 | Transpose | 블록체인 데이터 웨어하우스 | https://www.transpose.io |

---

## 1️⃣5️⃣ DAO & 거버넌스 (DAO & Governance)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 15.1 | Snapshot | 분산 투표 플랫폼 | https://snapshot.org |
| 15.2 | Tally | 온체인 거버넌스 대시보드 | https://www.tally.xyz |
| 15.3 | Aragon | DAO 운영 및 거버넌스 프레임워크 | `npm install @aragon/sdk` |
| 15.4 | Governor (OpenZeppelin) | OpenZeppelin Governor 계약 | `npm install @openzeppelin/contracts` |
| 15.5 | Colony | 조직 및 자금 관리 플랫폼 | https://colony.io |
| 15.6 | Curve DAO Governance | Curve 프로토콜 거버넌스 | https://curve.fi |
| 15.7 | Aave Governance | Aave 프로토콜 거버넌스 | https://governance.aave.com |
| 15.8 | Compound Governance | Compound 프로토콜 거버넌스 | `npm install @compound-finance/compound-governance` |
| 15.9 | Moloch DAO Framework | Moloch V2/V3 DAO 프레임워크 | https://github.com/MolochVentures |
| 15.10 | Gnosis Guild | Gnosis Safe 기반 DAO 도구 | https://www.gnosisguild.org |

---

## 🔗 추가 카테고리: 통합 도구 & 플랫폼

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 16.1 | Moralis Web3 API | Web3 데이터 통합 플랫폼 | `npm install moralis @moralisweb3/common` |
| 16.2 | Alchemy Enhanced API | Alchemy 고급 기능 (NFT, 토큰) | https://docs.alchemy.com |
| 16.3 | QuickNode Enhanced API | QuickNode JSON-RPC 확장 API | https://docs.quicknode.com |
| 16.4 | Web3 Onboard | 다중 지갑 통합 라이브러리 | `npm install @web3-onboard/core` |
| 16.5 | ERC Standards Registry | ERC 표준 공식 레지스트리 | https://eips.ethereum.org |
| 16.6 | Etherscan Smart Contracts | 검증된 컨트랙트 소스 | https://etherscan.io/contractsVerified |
| 16.7 | Remix IDE | 온라인 Solidity 개발 및 배포 | https://remix.ethereum.org |
| 16.8 | VS Code Solidity Extension | Solidity 언어 지원 확장 | `code --install-extension JuanBlanco.solidity` |

---

## 📌 핵심 리소스 & 링크

### 공식 문서
- **Ethereum**: https://ethereum.org/en/developers/
- **Solana**: https://docs.solana.com/
- **Polygon**: https://polygon.technology/
- **Arbitrum**: https://docs.arbitrum.io/
- **OpenZeppelin Contracts**: https://docs.openzeppelin.com/contracts/

### 커뮤니티 & 학습
- **Ethereum Stack Exchange**: https://ethereum.stackexchange.com/
- **r/ethereum**: https://www.reddit.com/r/ethereum/
- **CryptoDevHub**: https://cryptodevhub.io/

### 보안 가이드
- **OWASP Smart Contract Top 10**: https://owasp.org/www-project-smart-contract-top-10/
- **Immunefi Guides**: https://immunefi.com/guides/

---

## 🎯 사용 패턴

### 신규 DeFi 프로젝트
1. **개발**: Hardhat + ethers.js + wagmi
2. **테스트**: Foundry + Echidna
3. **배포**: Hardhat Ignition + Infura/Alchemy
4. **분석**: Dune Analytics + The Graph

### NFT 마켓플레이스
1. **스마트 컨트랙트**: Solidity + OpenZeppelin ERC721A
2. **프론트엔드**: viem + RainbowKit + thirdweb SDK
3. **저장소**: Pinata (IPFS) 또는 Arweave
4. **인덱싱**: The Graph 또는 Covalent API

### L2 마이그레이션
1. **선택**: Optimism (EVM 호환) vs zkSync (성능)
2. **브릿지**: Across Protocol 또는 네이티브 브릿지
3. **테스트**: Anvil (로컬 시뮬레이션)
4. **모니터링**: Dune Analytics + LayerZero 메시징

### 크로스체인 DAO
1. **거버넌스**: Snapshot (오프체인) + Governor (온체인)
2. **메시징**: LayerZero + Wormhole
3. **제안**: Tally 또는 Aragon
4. **실행**: Safe 멀티시그

---

## ✅ 점검 리스트

| 항목 | 확인 |
|------|------|
| 프로젝트 언어 선택 (Solidity/Vyper/Rust) | ☐ |
| 개발 환경 설정 (Hardhat/Foundry) | ☐ |
| RPC 제공자 선택 (Infura/Alchemy/QuickNode) | ☐ |
| 지갑 통합 (MetaMask/WalletConnect) | ☐ |
| 테스트 커버리지 (Foundry/Hardhat) | ☐ |
| 보안 감사 (Slither/Mythril/Certora) | ☐ |
| 배포 체인 선택 (L1/L2) | ☐ |
| 크로스체인 필요성 검토 (LayerZero/Wormhole) | ☐ |
| 데이터 인덱싱 (The Graph/Dune) | ☐ |
| DAO 거버넌스 구조 (Snapshot/Governor) | ☐ |

---

**총 도구: 140개 | 마지막 갱신: 2026-05-20 | 유지보수: orchestration_v1**
