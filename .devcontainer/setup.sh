#!/bin/bash

echo "🔧 Configurando entorno de desarrollo Crawl4AI..."

if [ -S /var/run/docker.sock ]; then
    echo "🐳 Configurando permisos de Docker..."
    sudo chmod 666 /var/run/docker.sock
    echo "✅ Permisos de Docker configurados"
fi

if [ -f .pre-commit-config.yaml ]; then
    echo "📌 Instalando pre-commit hooks..."
    pre-commit install
fi

mkdir -p tests/{unit,integration,fixtures,mcp}
mkdir -p docs/{api,guides,examples}
mkdir -p scripts
mkdir -p .vscode

if [ ! -f pytest.ini ]; then
    echo "📝 Creando configuración de pytest..."
    cat > pytest.ini << EOF
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers --cov=crawl4ai --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    mcp: MCP protocol tests
EOF
fi

if [ ! -f .vscode/launch.json ]; then
    echo "🐛 Configurando debugging para VS Code..."
    mkdir -p .vscode
    cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Crawl4AI Server",
            "type": "python",
            "request": "launch",
            "module": "crawl4ai.server",
            "justMyCode": false,
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": false
        },
        {
            "name": "Python: Debug Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["-v", "-s"],
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
EOF
fi

echo "📦 Instalando Crawl4AI en modo desarrollo..."
cd /workspace
pip install -e ".[all]"

echo "🎭 Configurando Playwright..."
playwright install chromium
crawl4ai-setup || echo "⚠️ crawl4ai-setup no disponible todavía"

echo "🔍 Verificando instalación..."
python -c "import crawl4ai; print('✅ Crawl4AI importado correctamente')" || echo "❌ Error importando Crawl4AI"
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright instalado correctamente')" || echo "❌ Error con Playwright"

echo "🧪 Configurando entorno de testing..."
pip install pytest-mock pytest-benchmark pytest-timeout

echo ""
echo "✨ Configuración completada!"
echo ""
echo "🚀 Comandos útiles:"
echo "   dev      - Ejecutar servidor Crawl4AI"
echo "   test     - Ejecutar tests"
echo "   fmt      - Formatear código"
echo "   crawl    - Ejecutar crawl4ai-doctor y servidor"
echo ""
echo "📚 Documentación:"
echo "   - API Server: http://localhost:11235"
echo "   - Playground: http://localhost:11235/playground"
echo "   - MCP WebSocket: ws://localhost:11235/mcp/ws"
echo "   - MCP SSE: http://localhost:11235/mcp/sse" 