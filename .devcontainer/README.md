# 🚀 Crawl4AI Dev Container

Entorno de desarrollo completo para Crawl4AI con todas las herramientas y servicios preconfigurados.

## 🎯 Características

- **Python 3.12** con todas las dependencias
- **Docker-in-Docker** para gestión de contenedores
- **Redis** para cache y cola de tareas
- **API Server** de Crawl4AI preconfigurado
- **Playwright** con navegadores instalados
- **MCP (Model Context Protocol)** integrado
- **VS Code** con extensiones optimizadas

## 📦 Cómo Usar

### 1. Abrir en Dev Container

**Opción A: VS Code**

1. Instala la extensión "Dev Containers"
2. Abre el proyecto Crawl4AI
3. Presiona `F1` → "Dev Containers: Reopen in Container"
4. Espera ~5-10 minutos la primera vez

**Opción B: Cursor**

1. Abre el proyecto
2. Cursor detectará automáticamente el dev container
3. Acepta abrir en contenedor

### 2. Servicios Disponibles

Al iniciar, tendrás acceso a:

- **API de Crawl4AI**: http://localhost:11235
- **Playground**: http://localhost:11235/playground
- **Redis**: redis://localhost:6379
- **MCP SSE**: http://localhost:11235/mcp/sse
- **MCP WebSocket**: ws://localhost:11235/mcp/ws

### 3. Comandos Útiles

```bash
# Desarrollo
dev         # Ejecutar servidor Crawl4AI
crawl       # crawl4ai-doctor + servidor
test        # Ejecutar tests con pytest
fmt         # Formatear código (black + ruff)

# Git
gs          # git status
gp          # git pull
gc          # git commit
gco         # git checkout

# Docker
docker-compose ps      # Ver servicios
docker-compose logs -f # Ver logs
```

## 🔧 Configuración

### Variables de Entorno

El archivo `.env.dev` contiene todas las variables mockeadas:

- API keys de LLM (valores de prueba)
- Configuración de Redis
- Configuración del servidor

### MCP (Model Context Protocol)

El servidor MCP se conecta automáticamente en VS Code. Puedes usar:

```python
# Test manual de MCP
from mcp import Client
client = Client("http://localhost:11235/mcp/sse")
tools = await client.list_tools()
```

### Debugging

Configuraciones de debug disponibles:

- `Python: Crawl4AI Server` - Debug del servidor
- `Python: Current File` - Debug archivo actual
- `Python: Debug Tests` - Debug de tests

## 🧪 Testing

```bash
# Ejecutar todos los tests
test

# Test específico
pytest tests/test_crawler.py -v

# Test con coverage
pytest --cov=crawl4ai --cov-report=html

# Test de integración
pytest -m integration
```

## 📚 Desarrollo

### Estructura del Proyecto

```
crawl4ai/
├── .devcontainer/      # Configuración del dev container
├── crawl4ai/           # Código fuente principal
├── tests/              # Tests unitarios e integración
├── docs/               # Documentación
└── deploy/docker/      # Archivos de deployment
```

### Flujo de Trabajo

1. **Editar código** en `/workspace`
2. **Hot reload** automático del servidor
3. **Tests** se ejecutan con `pytest`
4. **Formateo** automático al guardar

### Agregar Dependencias

```bash
# Agregar al proyecto
pip install nueva-dependencia
pip freeze > requirements.txt

# Reconstruir imagen si es necesario
docker-compose build crawl4ai-api
```

## 🐛 Solución de Problemas

### Los servicios no arrancan

```bash
# Verificar estado
docker-compose ps

# Reiniciar servicios
docker-compose restart

# Ver logs
docker-compose logs crawl4ai-api
```

### Problemas con Playwright

```bash
# Reinstalar navegadores
playwright install chromium --with-deps

# Verificar instalación
crawl4ai-doctor
```

### Redis no conecta

```bash
# Verificar Redis
redis-cli -h redis ping

# Reiniciar Redis
docker-compose restart redis
```

## 🚀 Tips Avanzados

### Ejecutar Crawl Local

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def test():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com")
        print(result.markdown)
```

### Conectar con API Remota

```python
from crawl4ai.docker_client import Crawl4AIDockerClient

async with Crawl4AIDockerClient(
    base_url="http://crawl4ai-api:11235"
) as client:
    results = await client.crawl(["https://example.com"])
```

### Monitoreo

```bash
# CPU/Memoria
docker stats

# Logs en tiempo real
docker-compose logs -f --tail=100

# Health checks
curl http://localhost:11235/health
```

## 📝 Notas

- El contenedor usa el usuario `vscode` (no root)
- Los cambios se sincronizan automáticamente
- Las extensiones de VS Code se persisten
- El cache de Playwright se mantiene entre sesiones

¡Listo para desarrollar! 🎉
