#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Iniciando entorno de desarrollo Crawl4AI${NC}"

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker no está disponible${NC}"
    
    echo -e "${YELLOW}🔧 Intentando arreglar permisos de Docker...${NC}"
    
    if ! groups $USER | grep -q docker; then
        sudo usermod -aG docker $USER
        echo -e "${YELLOW}📝 Usuario agregado al grupo docker. Puede ser necesario reiniciar el contenedor.${NC}"
    fi
    
    if [ -S /var/run/docker.sock ]; then
        sudo chmod 666 /var/run/docker.sock
        echo -e "${GREEN}✅ Permisos del socket de Docker arreglados${NC}"
    fi
    
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Todavía no se puede acceder a Docker. Por favor reinicia el contenedor.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Docker está accesible${NC}"

echo -e "${BLUE}🔍 Verificando servicios...${NC}"
echo -e "${YELLOW}⏳ Esperando a que los servicios estén listos...${NC}"

check_redis() {
    redis-cli -h redis ping >/dev/null 2>&1
}

check_api() {
    curl -f http://crawl4ai-api:11235/health >/dev/null 2>&1
}

MAX_RETRIES=30
RETRY_COUNT=0

echo -n "Verificando Redis..."
while ! check_redis && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo -n "."
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if check_redis; then
    echo -e " ${GREEN}✅ Redis está listo${NC}"
else
    echo -e " ${RED}❌ Redis no está disponible${NC}"
fi

RETRY_COUNT=0
echo -n "Verificando API de Crawl4AI..."
while ! check_api && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo -n "."
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if check_api; then
    echo -e " ${GREEN}✅ API de Crawl4AI está lista${NC}"
else
    echo -e " ${YELLOW}⚠️ API de Crawl4AI todavía no está lista${NC}"
    echo -e "${BLUE}💡 Puedes iniciarla manualmente con: docker-compose up crawl4ai-api${NC}"
fi

cat > /tmp/test_crawl4ai.py << 'EOF'
#!/usr/bin/env python3
"""
Test rápido de Crawl4AI
"""
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def test_basic_crawl():
    print("🧪 Probando crawl básico...")
    try:
        browser_config = BrowserConfig(headless=True)
        crawler_config = CrawlerRunConfig(cache_mode="bypass")
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url="https://httpbin.org/html",
                config=crawler_config
            )
            
            if result.success:
                print(f"✅ Crawl exitoso! Contenido: {len(result.markdown)} caracteres")
                return True
            else:
                print(f"❌ Crawl falló: {result.error}")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_basic_crawl())
    exit(0 if success else 1)
EOF

chmod +x /tmp/test_crawl4ai.py

echo -e "${BLUE}🧪 Ejecutando test de Crawl4AI...${NC}"
if python /tmp/test_crawl4ai.py; then
    echo -e "${GREEN}✅ Crawl4AI funciona correctamente${NC}"
else
    echo -e "${YELLOW}⚠️ Crawl4AI tuvo problemas en el test${NC}"
fi

echo -e "${GREEN}🎉 Entorno listo!${NC}"
echo -e "${BLUE}📊 Estado de servicios:${NC}"
docker-compose ps

echo -e ""
echo -e "${BLUE}🌐 Servicios disponibles:${NC}"
echo -e "  📡 API de Crawl4AI: http://localhost:11235"
echo -e "  🎮 Playground: http://localhost:11235/playground"
echo -e "  💾 Redis: redis://localhost:6379"
echo -e ""
echo -e "${BLUE}🤖 Endpoints MCP:${NC}"
echo -e "  📨 SSE: http://localhost:11235/mcp/sse"
echo -e "  🔌 WebSocket: ws://localhost:11235/mcp/ws"
echo -e ""
echo -e "${BLUE}🔧 Herramientas de desarrollo:${NC}"
echo -e "  🧪 Test local: python /tmp/test_crawl4ai.py"
echo -e "  📋 Ver logs: docker-compose logs -f crawl4ai-api"
echo -e "  🔄 Reiniciar API: docker-compose restart crawl4ai-api" 