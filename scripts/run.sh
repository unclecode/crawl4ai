#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 도움말 함수
show_help() {
    echo -e "${GREEN}Crawl4AI 실행 스크립트${NC}"
    echo "사용법: $0 [옵션]"
    echo
    echo "옵션:"
    echo "  -h, --help          도움말 표시"
    echo "  -b, --build         새로 빌드 후 실행"
    echo "  -d, --detach        백그라운드에서 실행"
    echo "  -l, --logs          로그 확인"
    echo "  -s, --stop          컨테이너 중지"
    echo "  -r, --restart       컨테이너 재시작"
    echo "  -t, --type TYPE     설치 타입 지정 (basic|torch|transformer|all)"
    echo "  -v, --version VER   버전 지정"
    echo
    echo "예시:"
    echo "  $0 -b -t all        # 전체 기능 설치로 새로 빌드 후 실행"
    echo "  $0 -d              # 백그라운드에서 실행"
    echo "  $0 -l              # 로그 확인"
}

# 기본값 설정
PROFILE="local-arm64"
INSTALL_TYPE="basic"
VERSION="basic"
DETACH=false
BUILD=false
SHOW_LOGS=false
STOP=false
RESTART=false

# 인자 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -d|--detach)
            DETACH=true
            shift
            ;;
        -l|--logs)
            SHOW_LOGS=true
            shift
            ;;
        -s|--stop)
            STOP=true
            shift
            ;;
        -r|--restart)
            RESTART=true
            shift
            ;;
        -t|--type)
            INSTALL_TYPE="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}알 수 없는 옵션: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Docker Compose 명령어 구성
COMPOSE_CMD="docker-compose --profile $PROFILE"

# 환경 변수 설정
export INSTALL_TYPE
export VERSION

# 실행 로직
if [ "$STOP" = true ]; then
    echo -e "${YELLOW}컨테이너 중지 중...${NC}"
    $COMPOSE_CMD down
elif [ "$RESTART" = true ]; then
    echo -e "${YELLOW}컨테이너 재시작 중...${NC}"
    $COMPOSE_CMD restart
elif [ "$SHOW_LOGS" = true ]; then
    echo -e "${YELLOW}로그 확인 중...${NC}"
    $COMPOSE_CMD logs -f
elif [ "$BUILD" = true ]; then
    echo -e "${YELLOW}이미지 새로 빌드 중...${NC}"
    $COMPOSE_CMD build --no-cache
fi

if [ "$STOP" = false ] && [ "$SHOW_LOGS" = false ]; then
    if [ "$DETACH" = true ]; then
        echo -e "${YELLOW}백그라운드에서 실행 중...${NC}"
        $COMPOSE_CMD up -d
    else
        echo -e "${YELLOW}실행 중...${NC}"
        $COMPOSE_CMD up
    fi
fi

echo -e "${GREEN}완료!${NC}" 