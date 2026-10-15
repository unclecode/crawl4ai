# Crawl4AI library plus the self-hosted API/MCP server (deploy/docker).
#
# The MCP endpoint is not part of the library. It is the FastAPI server under
# deploy/docker, which speaks SSE at /mcp/sse and drives Playwright Chromium.
#
# nixpkgs has no unclecode-litellm pin and no patchright/alphashape. LLM calls
# use nixpkgs litellm (imported lazily, not on the fetch/screenshot path).
# Undetected-browser mode (patchright) is not installed; the server's default
# browser path uses Playwright. alphashape is declared upstream and unused.
{
  lib,
  stdenv,
  src,
  python3,
  redis,
  openssl,
  playwright-driver,
  writeShellScriptBin,
}:
let
  versionFile = builtins.readFile "${src}/crawl4ai/__version__.py";
  versionLine = lib.findFirst (line: lib.hasPrefix "__version__ = " line) (
    throw "crawl4ai: __version__ assignment missing in ${src}/crawl4ai/__version__.py"
  ) (lib.splitString "\n" versionFile);
  version = builtins.head (
    builtins.match "__version__ = \"([0-9.]+)\"" versionLine
  );

  py = python3.pkgs;

  crawl4ai = py.buildPythonPackage {
    pname = "crawl4ai";
    inherit version src;

    pyproject = true;

    build-system = with py; [
      setuptools
      wheel
    ];

    # setup.py creates ~/.crawl4ai as an import side effect. Nix builds with
    # HOME=/homeless-shelter, so that mkdir fails. The cache is runtime state.
    postPatch = ''
      awk '
        /Create the \.crawl4ai folder/ { skip = 1 }
        skip && /^version = / { skip = 0 }
        !skip { print }
      ' setup.py > setup.py.new
      mv setup.py.new setup.py
    '';

    # Importing crawl4ai creates $CRAWL4_AI_BASE_DIRECTORY/.crawl4ai.
    preInstall = ''
      export HOME=$(mktemp -d)
      export CRAWL4_AI_BASE_DIRECTORY=$HOME
    '';

    # Upstream pins (snowballstemmer~=2.2, lxml<7, unclecode-litellm==…) do not
    # match nixpkgs. Relax them and drop deps we do not ship.
    pythonRelaxDeps = true;
    pythonRemoveDeps = [
      "unclecode-litellm"
      "patchright"
      "alphashape"
    ];

    dependencies = with py; [
      aiofiles
      aiohttp
      aiosqlite
      anyio
      beautifulsoup4
      brotli
      chardet
      click
      cssselect
      fake-useragent
      httpx
      humanize
      lark
      litellm
      lxml
      nltk
      numpy
      pillow
      playwright
      playwright-stealth
      psutil
      pydantic
      pyopenssl
      python-dotenv
      pyyaml
      rank-bm25
      requests
      rich
      shapely
      snowballstemmer
      xxhash
    ];

    pythonImportsCheck = [ "crawl4ai" ];

    doCheck = false;

    meta = {
      description = "LLM-friendly web crawler and scraper";
      homepage = "https://github.com/unclecode/crawl4ai";
      license = lib.licenses.asl20;
      platforms = lib.platforms.linux;
    };
  };

  serverDeps = with py; [
    crawl4ai
    aiohttp
    anyio
    dnspython
    email-validator
    fastapi
    gunicorn
    httpx
    mcp
    prometheus-fastapi-instrumentator
    pydantic
    pyjwt
    pypdf
    pyyaml
    rank-bm25
    redis
    slowapi
    sse-starlette
    uvicorn
    websockets
  ];

  pythonEnv = python3.withPackages (_: serverDeps);

  serverRoot = stdenv.mkDerivation {
    pname = "crawl4ai-server-root";
    inherit version src;
    dontConfigure = true;
    dontBuild = true;
    installPhase = ''
      mkdir -p "$out"
      cp deploy/docker/*.py deploy/docker/config.yml "$out/"
      rm -f "$out"/test-websocket.py
      cp -r deploy/docker/static "$out/static"
      # _resolve_auth() trusts config.yml's app.host, not the gunicorn bind.
      # A non-loopback host plus CRAWL4AI_API_TOKEN is the supported exposure.
      substituteInPlace "$out/config.yml" \
        --replace-fail 'host: "127.0.0.1"' 'host: "0.0.0.0"'
    '';
  };

  browsers = playwright-driver.browsers;
in
writeShellScriptBin "crawl4ai-server" ''
  set -eu
  if [ -z "''${CRAWL4AI_API_TOKEN:-}" ]; then
    printf 'crawl4ai-server: CRAWL4AI_API_TOKEN is unset\n' >&2
    exit 1
  fi
  if [ -z "''${REDIS_PASSWORD:-}" ]; then
    printf 'crawl4ai-server: REDIS_PASSWORD is unset\n' >&2
    exit 1
  fi
  export PYTHONUNBUFFERED=1
  export PYTHONDONTWRITEBYTECODE=1
  export PLAYWRIGHT_BROWSERS_PATH=${lib.escapeShellArg browsers}
  export PATH=${lib.escapeShellArg (lib.makeBinPath [ redis openssl pythonEnv ])}:$PATH
  cd ${lib.escapeShellArg serverRoot}
  exec ${lib.escapeShellArg "${pythonEnv}/bin/gunicorn"} \
    --bind "''${GUNICORN_BIND:-0.0.0.0:11235}" \
    --workers 1 \
    --threads 4 \
    --timeout 1800 \
    --graceful-timeout 30 \
    --keep-alive 300 \
    --worker-class uvicorn.workers.UvicornWorker \
    --log-level info \
    server:app
''
// {
  inherit version;
  passthru = {
    inherit crawl4ai pythonEnv serverRoot browsers redis;
  };
  meta = {
    description = "Crawl4AI API and MCP server";
    homepage = "https://github.com/unclecode/crawl4ai";
    license = lib.licenses.asl20;
    mainProgram = "crawl4ai-server";
    platforms = lib.platforms.linux;
  };
}
