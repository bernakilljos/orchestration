# GIS & Mapping Toolkit

> **목적**: 공간 데이터·지도 기반 프로젝트의 공통 도구 모음 (80+ 도구)
> **적용 범위**: 위치 기반 서비스 · 지도 시각화 · 공간 분석 · 라우팅 · 위성 이미지
> **카테고리**: 10개 영역 · 도구·API·라이브러리·서비스별 분류

---

## 1. 지도 라이브러리 (Web Frontend)

### 오픈소스 / 상용 비교

| 도구 | 유형 | 기반 | 강점 | 약점 | 설치 |
|---|---|---|---|---|---|
| **Leaflet** | 오픈소스 | Raster + Vector | 경량 · 모바일 최적 · 문서 풍부 | 3D 약함 · 고급 기능 제한 | `npm install leaflet` |
| **Mapbox GL JS** | 상용 | WebGL | 벡터 기반 · 3D 지형 · 실시간 데이터 | 유료 · API quota 제한 | `npm install mapbox-gl` |
| **OpenLayers** | 오픈소스 | Canvas + WebGL | 기능 풍부 · GIS 전문 · 레이어 관리 | 학습곡선 가파름 | `npm install ol` |
| **Google Maps API** | 상용 | JavaScript SDK | 글로벌 데이터 · 검색 통합 · 예측 · 신뢰도 | 가격 · quota · API key 관리 | `<script src="https://maps.googleapis.com/maps/api/js?key=...">` |
| **Kakao Maps API** | 상용 (한국) | JavaScript SDK | 한국 지도 정확도 · 로컬 서비스 | 한국만 · 해외 미지원 | `<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=...">` |
| **Naver Maps API** | 상용 (한국) | JavaScript SDK | 한국 POI · 실시간 교통 · 위성 이미지 | 한국만 · 영어 문서 부족 | `<script src="https://openapi.map.naver.com/openapi/v3/maps.js?ncpClientId=...">` |
| **deck.gl** | 오픈소스 | WebGL | 대규모 데이터 시각화 · 성능 · Mapbox 연동 | 단순 지도 위치에 한계 | `npm install deck.gl` |
| **Maplibre GL JS** | 오픈소스 | WebGL | Mapbox GL 무료 포크 · 오픈소스 대체 | 커뮤니티 작음 | `npm install maplibre-gl` |
| **Folium** | 오픈소스 (Python) | Leaflet | Jupyter 통합 · 지오팬다 연동 | 상호작용 제한 | `pip install folium` |
| **Cesium.js** | 오픈소스 | WebGL | 3D 지형 · 위성 이미지 · 비행 시뮬레이션 | 무거움 · 러닝커브 | `npm install cesium` |

### 선택 기준
- **경량 웹 매핑** → Leaflet
- **3D + 벡터** → Mapbox GL / Cesium
- **한국 기반** → Kakao / Naver
- **데이터 시각화** → deck.gl + Mapbox
- **GIS 전문** → OpenLayers
- **대화형 분석** → Folium (Python 환경)

---

## 2. 지오코딩 & 역지오코딩 (주소 ↔ 좌표)

| 도구 | API Type | 한국 지원 | 정확도 | 가격 | API 호출 |
|---|---|---|---|---|---|
| **Nominatim** (OpenStreetMap) | REST |  (OSM 기반) | 중간 | 무료 | `GET /search?q=...&format=json` |
| **Google Geocoding API** | REST |  | 높음 | $0.005/req (5000/일 무료) | `https://maps.googleapis.com/maps/api/geocode/json?address=...` |
| **Mapbox Geocoding API** | REST |  | 높음 | $0.50/1000 requests | `https://api.mapbox.com/geocoding/v5/...` |
| **Kakao Local API** | REST |  최고 | 최고 (한국) | 무료 (25만/일) | `https://dapi.kakao.com/v2/local/search/address.json?query=...` |
| **Naver Geocoding API** | REST |  최고 | 최고 (한국) | 무료 (5만/일) | `https://naveropenapi.apigw.ntruss.com/map-geocoding/v2/geocode?query=...` |
| **AWS Location Service** | REST |  | 높음 | $0.40/1000 requests | `https://geo.us-east-1.amazonaws.com/...` |
| **Azure Maps** | REST |  | 높음 | $0.50/1000 requests | `https://atlas.microsoft.com/search/address/json?...` |

### 한국 특화 전략
```bash
# 우선순위: Kakao (최고 정확도) → Naver (백업) → Google (국제)
# 라운드로빈으로 quota 분산
```

---

## 3. 공간 데이터베이스 (GIS DB)

| DB | 지원 | 강점 | 설치 | 쿼리 예시 |
|---|---|---|---|---|
| **PostGIS** (PostgreSQL 확장) | Point · Polygon · LineString · Raster | 성숙도 · 표준 OGC · 래스터 지원 | `apt install postgis`, `CREATE EXTENSION postgis;` | `SELECT * FROM table WHERE ST_Distance(geom, ST_Point(0,0)) < 1000;` |
| **SpatiaLite** (SQLite 확장) | Point · Polygon · LineString | 경량 · 파일 기반 · 모바일 | `spatialite my.db`, `SELECT load_extension('mod_spatialite');` | `SELECT * FROM table WHERE ST_Distance(geom, GeomFromText('POINT(0 0)')) < 1000;` |
| **MongoDB GeoJSON** | Point · Polygon · LineString | NoSQL · 유연 · 실시간 | `npm install mongodb`, `createIndex({ location: "2dsphere" })` | `db.collection.find({ location: { $near: { $geometry: {...} } } })` |
| **Elasticsearch Geo** | Point · Shape (Polygon) | 검색 최적화 · 대규모 데이터 | `docker run -d docker.elastic.co/elasticsearch/elasticsearch:...` | `GET /_search { "query": { "geo_distance": { "location": {...} } } }` |
| **MySQL Spatial** | Point · Polygon · LineString (MySQL 5.7+) | 광범위 호스팅 | MySQL 5.7+ 기본 포함 | `SELECT * FROM table WHERE ST_Distance_Sphere(geom, ST_Point(0,0)) < 1000;` |
| **DuckDB Spatial** | Vector (Point · Polygon) · Raster | 분석 성능 · OLAP | `pip install duckdb`, `INSTALL spatial; LOAD spatial;` | `SELECT * FROM read_parquet(...) WHERE ST_DWithin(geom, ST_Point(0,0), 1000);` |

---

## 4. 공간 분석 & 데이터 처리 (Python)

### 핵심 라이브러리 스택

```bash
# GIS 분석 핵심
pip install geopandas shapely fiona gdal rasterio folium

# 설명별 설치
pip install geopandas       # 지오팬다 — GIS 벡터 분석 (pandas 확장)
pip install shapely         # 기하학 연산 (buffer · intersection · union)
pip install fiona          # 벡터 I/O (shapefile · GeoJSON · GML)
pip install rasterio       # 래스터 I/O (GeoTIFF · HDF5)
pip install folium         # Leaflet 래퍼 (Jupyter 대화형)
pip install pyproj         # 좌표계 변환 (WGS84 ↔ Web Mercator)
pip install rtree          # 공간 인덱싱 (대규모 쿼리 성능)
```

### 자주 쓰는 패턴

```python
import geopandas as gpd
from shapely.geometry import Point, Polygon

# 벡터 로드 & 필터
gdf = gpd.read_file("data.shp")
gdf_filtered = gdf[gdf.geometry.distance(Point(0,0)) < 1000]

# 버퍼 · 교집합
gdf['buffer'] = gdf.geometry.buffer(100)  # 100m 버퍼
gdf['intersection'] = gdf.geometry.intersection(boundary_polygon)

# 지도 시각화
gdf.plot(column='value', legend=True)
folium.Map(location=[37.5, 127], zoom_start=10)
```

---

## 5. 위성 이미지 & 원격감지

| 서비스 | 무료 여부 | 분해능 | 용도 | 가입 |
|---|---|---|---|---|
| **Google Earth Engine** | 무료 (교육/연구) | Sentinel-2: 10m, Landsat: 30m | 시계열 분석 · 대규모 처리 | `npm install @google/earthengine` |
| **Sentinel Hub** | 무료 한계 | Sentinel-1/2: 10m | 위성 이미지 스트리밍 · API | Copernicus 가입 |
| **Planet API** | 유료 ($) | 3m-50cm | 고해상도 · 상용 | `pip install planet` |
| **USGS Earth Explorer** | 무료 | 다양 | 미국 위성 데이터 | Landsat · Sentinel |
| **NASA MODIS** | 무료 | 250m-1000m | 환경 모니터링 · 기후 | `https://lpdaac.usgs.gov/` |
| **ESA Copernicus Hub** | 무료 | Sentinel 10m+ | 유럽 위성 데이터 | `scihub.copernicus.eu` |

### 한국 자원
- **국토정보플랫폼**: 항공 정사영상 (1m) 무료
- **V-World**: 항공/위성 이미지 + 지도 데이터
- **지적도 API**: 수치지적도 무료

---

## 6. 라우팅 & 네트워크 분석

| 도구 | 유형 | 가격 | 특징 | 설치/호출 |
|---|---|---|---|---|
| **OSRM** (Open Source Routing Machine) | 오픈소스 자체호스트 | 무료 | 경로 최적화 · 거리 행렬 | `docker run -d -p 5000:5000 osrm/osrm-backend:v5.27.1` |
| **GraphHopper** | 오픈소스 | 무료 + 상용 | 다중 경로 · 사용자정의 · 비용 최적화 | `java -Xmx4g -jar graphhopper-web-*.jar` |
| **Valhalla** | 오픈소스 | 무료 | 자동차 · 자전거 · 보행자 · 다중모달 | `docker run -d -p 8002:8002 gisops/valhalla:latest` |
| **Google Directions API** | 상용 | $0.005-0.02/req | 신뢰도 · 실시간 교통 · 대중교통 | `https://maps.googleapis.com/maps/api/directions/json?origin=...&destination=...` |
| **T-map API** (한국) | 상용 | 무료 (25만/일) | 한국 길찾기 · 실시간 교통 · 대중교통 | `https://api2.tmap.co.kr/routes?startX=...&startY=...` |
| **Kakao Directions API** | 상용 (한국) | 무료 (25만/일) | 한국 최적화 · 회피도로 · 톨게이트 | `https://apis.map.kakao.com/web/javascript/library/services.js` |
| **pgRouting** | PostgreSQL 확장 | 무료 | PostGIS 기반 · 네트워크 분석 | `CREATE EXTENSION pgrouting; SELECT ST_ShortestPath(...);` |
| **NetworkX** (Python) | 오픈소스 | 무료 | 그래프 분석 · 최단경로 · 중심성 | `pip install networkx` |

---

## 7. 3D 지형 & 시각화

| 라이브러리 | 기반 | 용도 | 설치 |
|---|---|---|---|
| **Cesium.js** | WebGL | 3D 지형 · 건물 · 비행 시뮬레이션 | `npm install cesium` |
| **Mapbox 3D Extrusion** | WebGL (GL JS) | 건물 3D · 고도 시각화 | Mapbox GL JS 기본 기능 |
| **deck.gl + Mapbox** | WebGL | 대규모 3D 시각화 · Point cloud | `npm install deck.gl mapbox-gl` |
| **Three.js** (with Mapbox) | WebGL | 커스텀 3D 모델 · 지형 오버레이 | `npm install three` |
| **Babylon.js** | WebGL | 게임 엔진 수준 3D · 물리 엔진 | `npm install babylonjs` |
| **A-Frame** (VR 지도) | WebGL (Three.js 기반) | VR/AR 공간 경험 · 몰입형 | `<script src="https://aframe.io/releases/1.4.0/aframe.min.js">` |

---

## 8. 모바일 위치 기반 서비스

### React Native / Flutter

| 도구 | 플랫폼 | 기능 | 설치 |
|---|---|---|---|
| **react-native-maps** | React Native | Apple Maps · Google Maps 네이티브 | `npm install react-native-maps` |
| **Google Maps Flutter Plugin** | Flutter | Google Maps 네이티브 | `flutter pub add google_maps_flutter` |
| **flutter_map** | Flutter | 오픈소스 · Leaflet 기반 | `flutter pub add flutter_map` |
| **Geolocation API** (웹) | 웹 모바일 | GPS · 가속도계 · 나침반 | `navigator.geolocation.getCurrentPosition(...)` |
| **Background Geolocation** | React Native | 백그라운드 위치 추적 | `npm install react-native-background-geolocation` |

### 한국 모바일 특화
```bash
# Kakao 모바일 지도
npm install react-native-kakao-maps  # React Native

# Naver 모바일 지도
flutter pub add naver_map_plugin  # Flutter
```

---

## 9. 한국 공간 데이터 & API

### 공식 플랫폼

| 플랫폼 | 데이터 | API | 가격 |
|---|---|---|---|
| **국토정보플랫폼** (NSDI) | 수치지도 · 항공 정사영상 (1m) · 지적도 · 도로명주소 | RESTful | 무료 (가입) |
| **V-World** (한국 국가 지오플랫폼) | 항공/위성 이미지 · 지도 · POI · 도로망 | WMS · WMTS · REST | 무료 (API Key) |
| **지적도 API** (대한민국 지적청) | 수치지적도 · 경계 데이터 | WMS · GeoJSON | 무료 |
| **도로명주소 API** (국토교통부) | 도로명 주소 검색 · 변환 | REST | 무료 (API Key) |
| **지형도 API** (국토정보공사) | 1:5000 · 1:25000 수치지형도 | WMS | 무료 |
| **한국철도공사 (KORAIL)** | 철도 네트워크 · 역 위치 | 공개 API | 무료 |
| **한국수자원공사 (K-water)** | 댐 · 강 유량 · 홍수 예측 | REST | 무료 |
| **한국원자력안전기술원** | 방사능 모니터링 데이터 | REST | 공개 |

### 자주 쓰는 변환 유틸
```bash
# 한국 좌표계 변환 라이브러리
pip install pyproj  # WGS84 ↔ EPSG:5179 (UTM-K)

# 도로명주소 파싱
pip install address-parser-korean
```

---

## 10. 실내 지도 & 네비게이션

| 도구 | 특징 | 설치 | 한국 |
|---|---|---|---|
| **Mappedin** | 상용 · 실내지도 전문 · 라우팅 | `npm install mappedin-sdk` | 일부 지원 |
| **IndoorAtlas** | 실내 위치추적 · BLE · WiFi | `npm install indooratlas-js-sdk` | 지원함 |
| **Steerpath** | 실내 네비게이션 · 3D 지도 | SDK | 제한적 |
| **OpenStreetMap Indoor** | 오픈소스 · 커뮤니티 | Leaflet + `indoorequality.js` | 소수 건물 |
| **HERE WeGo** (실내) | HERE Maps 실내 | HERE API | 일부 |

### 한국 쇼핑몰 / 공항 실내지도
- **Kakao Map**: 롯데월드몰 · 삼성역 등 주요 건물
- **Naver Map**: 인천공항 · 명동 · 강남역
- **SKT T-map**: 지하철역 · 공항 터미널

---

## 11. 학습 리소스

### 튜토리얼 & 문서
- **Leaflet 공식**: https://leafletjs.com/
- **Mapbox GL Docs**: https://docs.mapbox.com/mapbox-gl-js/
- **GeoPandas**: https://geopandas.org/
- **PostGIS**: https://postgis.net/
- **Google Earth Engine**: https://earthengine.google.com/
- **한국 공공 API 포털**: https://www.data.go.kr/

### 커뮤니티
- **GIS Stack Exchange**: https://gis.stackexchange.com/
- **OpenStreetMap**: https://www.openstreetmap.org/
- **QGIS (데스크톱 GIS)**: https://qgis.org/

---

## 12. 선택 의사결정도

```text
프로젝트 요구사항?
├─ 웹 지도 표시
│  ├─ 가벼움 + 기본 기능 → Leaflet
│  ├─ 3D + 벡터 → Mapbox GL JS
│  └─ 한국 기반 → Kakao / Naver
├─ 공간 분석 (Python)
│  ├─ 벡터 데이터 → GeoPandas + Shapely
│  ├─ 위성 이미지 → Google Earth Engine / rasterio
│  └─ 대규모 데이터 → DuckDB Spatial
├─ 라우팅 & 네트워크
│  ├─ 자체호스트 → OSRM / GraphHopper
│  ├─ 한국 최적화 → T-map / Kakao
│  └─ 실시간 교통 → Google Directions
├─ 실내 네비게이션
│  └─ Mappedin / IndoorAtlas
└─ 3D 지형 & 시뮬레이션
   └─ Cesium.js / deck.gl
```

---

## 13. 마이그레이션 팁

### Leaflet → Mapbox GL JS
```javascript
// Leaflet
L.map('map').setView([37.5, 127], 12);

// Mapbox GL JS (더 세밀한 스타일 & 3D)
mapboxgl.accessToken = 'pk_...';
new mapboxgl.Map({ container: 'map', style: 'mapbox://styles/mapbox/streets-v12', center: [127, 37.5], zoom: 12 });
```

### Google Maps → Mapbox
- **이점**: 오픈소스 · 커스터마이징 · 비용 절감
- **단점**: 학습곡선 · 데이터 정확도 (지역별)
- **마이그레이션 도구**: Mapbox Map ID migration guide

---

## 14. 비용 최적화

| 시나리오 | 권장 조합 |
|---|---|
| **스타트업** | Leaflet + OpenStreetMap + Kakao Geocoding (한국) + OSRM (자체호스트) |
| **중소 SaaS** | Mapbox GL JS + Google Directions API (quota 관리) |
| **엔터프라이즈** | PostGIS + deck.gl + GraphHopper 엔터프라이즈 + 한국 공공 데이터 |
| **연구/교육** | Google Earth Engine + GDAL + QGIS + 공개 좌표계 |

---

**최종 업데이트**: 2026-05-20
