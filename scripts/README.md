# Crawl4AI 실행 스크립트

이 디렉토리에는 Crawl4AI를 실행하기 위한 스크립트들이 포함되어 있습니다.

## 스크립트 목록

### run.sh
Mac M1 환경에서 Crawl4AI를 실행하기 위한 메인 스크립트입니다.

## 사용법

### 기본 실행
```bash
./run.sh
```

### 전체 기능 설치로 실행
```bash
./run.sh -t all
```

### 백그라운드에서 실행
```bash
./run.sh -d
```

### 새로 빌드 후 실행
```bash
./run.sh -b
```

### 로그 확인
```bash
./run.sh -l
```

### 컨테이너 중지
```bash
./run.sh -s
```

### 컨테이너 재시작
```bash
./run.sh -r
```

### 도움말 보기
```bash
./run.sh -h
```

## 옵션 설명

| 옵션 | 설명 | 예시 |
|------|------|------|
| `-h, --help` | 도움말 표시 | `./run.sh -h` |
| `-b, --build` | 새로 빌드 후 실행 | `./run.sh -b` |
| `-d, --detach` | 백그라운드에서 실행 | `./run.sh -d` |
| `-l, --logs` | 로그 확인 | `./run.sh -l` |
| `-s, --stop` | 컨테이너 중지 | `./run.sh -s` |
| `-r, --restart` | 컨테이너 재시작 | `./run.sh -r` |
| `-t, --type TYPE` | 설치 타입 지정 (basic\|torch\|transformer\|all) | `./run.sh -t all` |
| `-v, --version VER` | 버전 지정 | `./run.sh -v latest` |

## 설치 타입 설명

- `basic`: 기본 기능만 설치
- `torch`: PyTorch 관련 기능 추가 설치
- `transformer`: Transformer 모델 관련 기능 추가 설치
- `all`: 모든 기능 설치

## 실행 전 확인사항

1. Docker Desktop이 실행 중인지 확인
2. `.env` 파일이 올바르게 설정되어 있는지 확인
3. 충분한 디스크 공간이 있는지 확인

## 주의사항

- 이 스크립트는 Mac M1 환경에 최적화되어 있습니다 (ARM64 프로파일 사용)
- GPU 지원은 AMD64 플랫폼에서만 사용 가능합니다
- 메모리 제한은 기본적으로 4GB로 설정되어 있습니다 