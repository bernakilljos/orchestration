# Caching & Performance Toolkit

> **목적**: 캐싱·성능 최적화 관련 80+ 공통 도구 레퍼런스
> **적용**: 인메모리 캐시·CDN·프로파일링·번들 최적화 등
> **최신**: 2026-05-20

---

## 1. 인메모리 캐시 (In-Memory Cache)

### Redis
- **용도**: 고성능 캐시, 세션 저장소, 메시지 큐
- **특징**: 단일 스레드, 매우 빠름, 영속성 옵션
- **설치**:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install redis-server
  redis-server
  
  # macOS
  brew install redis
  brew services start redis
  
  # Docker
  docker run -d -p 6379:6379 redis:latest
  ```
- **Python 클라이언트**:
  ```bash
  pip install redis
  ```
  ```python
  import redis
  r = redis.Redis(host='localhost', port=6379, db=0)
  r.set('key', 'value')
  print(r.get('key'))
  r.expire('key', 60)  # 60초 TTL
  ```
- **Node.js 클라이언트**:
  ```bash
  npm install redis
  ```
  ```javascript
  const redis = require('redis');
  const client = redis.createClient();
  client.set('key', 'value');
  client.get('key', (err, reply) => console.log(reply));
  ```

### Memcached
- **용도**: 단순 캐시, 분산 메모리
- **특징**: TCP/IP 프로토콜, 더 간단한 구조
- **설치**:
  ```bash
  sudo apt-get install memcached
  memcached -p 11211
  
  # Docker
  docker run -d -p 11211:11211 memcached:latest
  ```
- **Python 클라이언트**:
  ```bash
  pip install pymemcache
  ```

### Dragonfly
- **용도**: Redis 호환 고성능 캐시 (최신)
- **특징**: 멀티스레드, 더 빠른 처리량
- **설치**:
  ```bash
  docker run -d -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly:latest
  ```

### KeyDB
- **용도**: Redis 호환 멀티스레드 버전
- **설치**:
  ```bash
  docker run -d -p 6379:6379 eqalpha/keydb:latest
  ```

### Hazelcast
- **용도**: Java 기반 분산 인메모리 캐시
- **설치** (Maven):
  ```xml
  <dependency>
    <groupId>com.hazelcast</groupId>
    <artifactId>hazelcast</artifactId>
    <version>5.3.0</version>
  </dependency>
  ```

---

## 2. 애플리케이션 캐시 (Application-Level Cache)

### Django Cache
- **설정** (`settings.py`):
  ```python
  CACHES = {
    'default': {
      'BACKEND': 'django.core.cache.backends.redis.RedisCache',
      'LOCATION': 'redis://127.0.0.1:6379/1',
    }
  }
  ```
- **사용**:
  ```python
  from django.core.cache import cache
  cache.set('key', 'value', 300)  # 5분 TTL
  print(cache.get('key'))
  ```

### Flask-Caching
- **설치**:
  ```bash
  pip install Flask-Caching
  ```
- **설정**:
  ```python
  from flask_caching import Cache
  cache = Cache(app, config={'CACHE_TYPE': 'redis'})
  
  @app.route('/data')
  @cache.cached(timeout=300)
  def get_data():
    return {"data": "..."}
  ```

### Spring Cache (Java)
- **설정** (`application.properties`):
  ```properties
  spring.cache.type=redis
  spring.redis.host=localhost
  spring.redis.port=6379
  ```
- **사용**:
  ```java
  @Service
  public class UserService {
    @Cacheable("users")
    public User getUser(Long id) {
      return userRepository.findById(id);
    }
  }
  ```

### node-cache
- **설치**:
  ```bash
  npm install node-cache
  ```
- **사용**:
  ```javascript
  const NodeCache = require('node-cache');
  const cache = new NodeCache({ stdTTL: 300 });
  cache.set('key', 'value');
  console.log(cache.get('key'));
  ```

---

## 3. CDN 캐시 (Content Delivery Network)

### Cloudflare
- **용도**: 글로벌 CDN, DDoS 방어
- **가격**: 무료 플랜 부터 시작
- **설정**: DNS 지점 후 자동 활성화
- **정책 설정**:
  ```text
  Caching Level: Standard / Aggressive
  Browser Cache TTL: 30 minutes / 1 hour / 1 month
  Cache Everything: 기본 비활성
  ```

### Amazon CloudFront (AWS)
- **용도**: AWS 관리형 CDN
- **설정** (AWS CLI):
  ```bash
  aws cloudfront create-distribution \
    --distribution-config file://distribution.json
  ```
- **캐시 제어**:
  ```json
  {
    "CacheBehaviors": [{
      "PathPattern": "/images/*",
      "DefaultTTL": 86400,
      "MaxTTL": 31536000
    }]
  }
  ```

### Fastly
- **용도**: 고성능 CDN, VCL (Varnish) 지원
- **가격**: 종량제 ($0.12/GB)
- **VCL 예시**:
  ```vcl
  sub vcl_recv {
    if (req.url ~ "^/images/") {
      set req.http.Cache-Control = "max-age=31536000";
    }
  }
  ```

### BunnyCDN
- **용도**: 저가형 CDN
- **가격**: $0.01/GB (가장 저렴)
- **대시보드**: https://panel.bunnycdn.com

### Akamai
- **용도**: 엔터프라이즈급 CDN
- **특징**: 높은 신뢰성, 복잡한 설정
- **가격**: 연간 $10,000+

---

## 4. 브라우저 캐시 (Browser Cache)

### Service Worker
- **예시** (`sw.js`):
  ```javascript
  self.addEventListener('install', event => {
    event.waitUntil(
      caches.open('v1').then(cache => {
        return cache.addAll(['/index.html', '/style.css', '/app.js']);
      })
    );
  });
  
  self.addEventListener('fetch', event => {
    event.respondWith(
      caches.match(event.request).then(response => {
        return response || fetch(event.request);
      })
    );
  });
  ```

### Cache API
- **직접 사용** (JavaScript):
  ```javascript
  caches.open('v1').then(cache => {
    cache.addAll(['/js/app.js', '/css/style.css']);
  });
  ```

### Workbox (Google)
- **설치**:
  ```bash
  npm install workbox-cli --save-dev
  npx workbox wizard --injectManifest
  ```
- **설정** (`workbox-config.js`):
  ```javascript
  module.exports = {
    globDirectory: 'dist/',
    globPatterns: ['**/*.{js,css,html}'],
    swDest: 'dist/sw.js'
  };
  ```

### PWA (Progressive Web App)
- **manifest.json**:
  ```json
  {
    "name": "My App",
    "icons": [{"src": "icon.png", "sizes": "192x192"}],
    "display": "standalone",
    "scope": "/",
    "service_worker": {"src": "/sw.js"}
  }
  ```

---

## 5. DB 쿼리 캐시 (Database Query Caching)

### Redis 캐싱 레이어
- **구조**: App → Redis → DB
- **패턴** (Python):
  ```python
  def get_user(user_id):
      cache_key = f"user:{user_id}"
      user = cache.get(cache_key)
      if not user:
          user = db.query(f"SELECT * FROM users WHERE id={user_id}")
          cache.set(cache_key, user, 3600)
      return user
  ```

### ProxySQL
- **용도**: MySQL 쿼리 캐싱 프록시
- **설치**:
  ```bash
  docker run -d --name proxysql \
    -p 6032:6032 -p 3306:3306 \
    proxysql/proxysql:latest
  ```

### PgBouncer
- **용도**: PostgreSQL 연결 풀링
- **설치**:
  ```bash
  sudo apt-get install pgbouncer
  ```
- **설정** (`pgbouncer.ini`):
  ```ini
  [databases]
  mydb = host=localhost port=5432 dbname=mydb
  
  [pgbouncer]
  pool_mode = transaction
  max_client_conn = 1000
  default_pool_size = 25
  ```

### MySQL Query Cache (레거시)
- **참고**: MySQL 8.0+ 에서 제거됨
- **대체**: Redis 또는 Memcached 사용

---

## 6. HTTP 캐시 (HTTP Caching Proxy)

### Varnish
- **용도**: HTTP 캐시, 역프록시
- **특징**: 매우 빠름, VCL 프로그래밍 가능
- **설치**:
  ```bash
  sudo apt-get install varnish
  varnishd -f /etc/varnish/default.vcl -s malloc,256m
  ```
- **VCL 설정** (`default.vcl`):
  ```vcl
  vcl 4.0;
  
  backend default {
    .host = "localhost";
    .port = "8080";
  }
  
  sub vcl_recv {
    if (req.method == "GET") {
      return (hash);
    }
  }
  
  sub vcl_backend_response {
    set beresp.ttl = 1h;
  }
  ```

### Nginx proxy_cache
- **설정** (`nginx.conf`):
  ```nginx
  proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m;
  
  server {
    location / {
      proxy_cache my_cache;
      proxy_cache_valid 200 1h;
      proxy_pass http://backend;
      add_header X-Cache-Status $upstream_cache_status;
    }
  }
  ```

### Squid
- **용도**: 앞서는 캐시 프록시 (오픈소스)
- **설치**:
  ```bash
  sudo apt-get install squid
  ```

### Apache Traffic Server
- **용도**: 고성능 캐시, CDN용
- **설치**:
  ```bash
  sudo apt-get install trafficserver
  ```

---

## 7. 프로파일링 (Profiling)

### py-spy (Python)
- **설치**:
  ```bash
  pip install py-spy
  ```
- **사용**:
  ```bash
  py-spy record -o profile.svg -- python app.py
  py-spy top --pid $(pgrep -f app.py)
  ```

### cProfile (Python 표준)
- **사용**:
  ```python
  import cProfile
  cProfile.run('my_function()')
  ```
- **분석**:
  ```bash
  python -m cProfile -s cumulative script.py
  ```

### line_profiler (Python)
- **설치**:
  ```bash
  pip install line_profiler
  ```
- **사용**:
  ```bash
  kernprof -l -v script.py
  ```

### memory_profiler (Python)
- **설치**:
  ```bash
  pip install memory-profiler
  ```
- **사용**:
  ```python
  @profile
  def my_function():
      ...
  ```
  ```bash
  python -m memory_profiler script.py
  ```

### clinic.js (Node.js)
- **설치**:
  ```bash
  npm install -g clinic
  ```
- **사용**:
  ```bash
  clinic doctor -- node app.js
  clinic flame -- node app.js
  ```

### 0x (Node.js)
- **설치**:
  ```bash
  npm install -g 0x
  ```
- **사용**:
  ```bash
  0x node app.js
  ```

---

## 8. 번들 최적화 (Bundle Optimization)

### Webpack
- **설치**:
  ```bash
  npm install --save-dev webpack webpack-cli
  ```
- **설정** (`webpack.config.js`):
  ```javascript
  module.exports = {
    mode: 'production',
    entry: './src/index.js',
    output: { filename: 'bundle.js' },
    optimization: {
      minimize: true,
      splitChunks: { chunks: 'all' }
    }
  };
  ```

### Vite
- **설치**:
  ```bash
  npm create vite@latest my-app -- --template react
  cd my-app && npm install
  npm run build
  ```
- **특징**: 매우 빠른 빌드, 네이티브 ESM

### esbuild
- **설치**:
  ```bash
  npm install --save-dev esbuild
  ```
- **사용**:
  ```bash
  npx esbuild src/index.js --bundle --minify --outfile=out.js
  ```

### SWC
- **설치**:
  ```bash
  npm install --save-dev swc-cli @swc/core
  ```
- **사용**:
  ```bash
  swc src -d dist
  ```

### Rollup
- **설치**:
  ```bash
  npm install --save-dev rollup
  ```
- **설정** (`rollup.config.js`):
  ```javascript
  export default {
    input: 'src/index.js',
    output: { file: 'dist/bundle.js', format: 'umd' }
  };
  ```

### Turbopack
- **용도**: Next.js 번들러 (최신, 고성능)
- **특징**: Rust 기반, 매우 빠름

---

## 9. 이미지 최적화 (Image Optimization)

### next/image (Next.js)
- **사용**:
  ```jsx
  import Image from 'next/image';
  
  export default function MyComponent() {
    return (
      <Image
        src="/image.jpg"
        alt="Description"
        width={800}
        height={600}
        quality={75}
      />
    );
  }
  ```
- **자동 최적화**: WebP, AVIF, 반응형 크기

### imgproxy
- **용도**: 이미지 프록시, 동적 리사이징
- **Docker**:
  ```bash
  docker run -d -p 8080:8080 darthsim/imgproxy
  ```
- **URL 예시**:
  ```text
  /resize/600x400/smart/upload.jpg
  ```

### Thumbor
- **용도**: 이미지 서비스, 필터 적용
- **설치**:
  ```bash
  pip install thumbor
  thumbor -l 0.0.0.0 -p 8888
  ```

### Cloudinary
- **용도**: 클라우드 이미지 관리 (SaaS)
- **가격**: 무료 플랜 (75K transformations/month)
- **URL 변환**:
  ```text
  https://res.cloudinary.com/demo/image/upload/w_400,h_300,c_fill/sample.jpg
  ```

---

## 10. DB 성능 (Database Performance)

### pg_stat_statements (PostgreSQL)
- **활성화** (`postgresql.conf`):
  ```ini
  shared_preload_libraries = 'pg_stat_statements'
  ```
- **쿼리**:
  ```sql
  SELECT query, calls, mean_exec_time
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC LIMIT 10;
  ```

### EXPLAIN ANALYZE
- **사용**:
  ```sql
  EXPLAIN ANALYZE SELECT * FROM users WHERE age > 18;
  ```
- **결과**: 쿼리 계획, 실제 실행 시간

### slow_query_log (MySQL)
- **활성화** (`my.cnf`):
  ```ini
  slow_query_log = 1
  long_query_time = 2
  log_queries_not_using_indexes = 1
  ```
- **분석**:
  ```bash
  mysqldumpslow /var/log/mysql/slow.log | head -20
  ```

### pt-query-digest (Percona)
- **설치**:
  ```bash
  sudo apt-get install percona-toolkit
  ```
- **사용**:
  ```bash
  pt-query-digest /var/log/mysql/slow.log
  ```

### VACUUM & ANALYZE (PostgreSQL)
- **유지보수**:
  ```sql
  VACUUM ANALYZE;
  ```

### 인덱스 최적화
- **생성**:
  ```sql
  CREATE INDEX idx_users_email ON users(email);
  ```
- **분석**:
  ```sql
  EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';
  ```

---

## 성능 최적화 통합 체크리스트

```bash
#!/bin/bash
# 성능 감사 스크립트

echo "1. 캐시 설정 확인"
redis-cli INFO memory

echo "2. 느린 쿼리 확인"
mysql -e "SHOW PROCESSLIST;" | grep -i sleep

echo "3. 번들 크기 확인"
npm run build
ls -lh dist/

echo "4. 이미지 크기 최적화"
find . -name "*.png" -o -name "*.jpg" | xargs identify -format "%f: %wx%h\n"

echo "5. CDN 캐시 상태"
curl -I https://your-cdn-url.com/static/file.js | grep -i cache

echo "성능 감사 완료"
```

---

## 참조

- Redis: https://redis.io/
- Varnish: https://varnish-cache.org/
- Webpack: https://webpack.js.org/
- Vite: https://vitejs.dev/
- Next.js Image: https://nextjs.org/docs/api-reference/next/image
- PostgreSQL EXPLAIN: https://www.postgresql.org/docs/current/sql-explain.html
