> These workspace rename steps were prepared but intentionally never executed; the local TULYA directory was retained.

# Augmentr Gate 3 — manual workspace relocation

Prepared 2026-09-27. This is a command plan, not a completion report. The folder
move, environment recreation and full tests from the new path have not been run.

## Changes already prepared

The local proxy flag is now `AUGMENTR_LOCAL_API_PROXY`. Its ten reference sites
are listed below. The affected six Vitest tests pass from the current location.
No Git remote, Vercel configuration, domain, package name or lockfile was changed.

| File and line | Exact replacement line |
| --- | --- |
| `next.config.ts:14` | `    return (process.env.NODE_ENV === "development" || process.env.AUGMENTR_LOCAL_API_PROXY === "1") && !process.env.VERCEL` |
| `.env.example:3` | `# AUGMENTR_LOCAL_API_PROXY=1` |
| `.github/workflows/ci.yml:43` | `          AUGMENTR_LOCAL_API_PROXY: '1'` |
| `README.md:47` | `$env:AUGMENTR_LOCAL_API_PROXY = "1"` |
| `README.md:53` | `Remove-Item Env:AUGMENTR_LOCAL_API_PROXY, Env:E2E_PRODUCTION, Env:E2E_REUSE_SERVERS` |
| `docs/deployment.md:39` | See the literal Markdown row below. |
| `tests/frontend/security.test.ts:10` | `  vi.stubEnv("AUGMENTR_LOCAL_API_PROXY", "1");` |
| `tests/frontend/security.test.ts:17` | `  vi.stubEnv("AUGMENTR_LOCAL_API_PROXY", "");` |
| `tests/frontend/security.test.ts:19` | `  vi.stubEnv("AUGMENTR_LOCAL_API_PROXY", "1");` |
| `tests/frontend/security.test.ts:26` | `  vi.stubEnv("AUGMENTR_LOCAL_API_PROXY", "");` |

```markdown
| `AUGMENTR_LOCAL_API_PROXY=1` | Local production integration build only. Adds the port-18000 rewrite to the build. Never configure on Vercel; the Vercel guard disables it regardless. |
```

This repository has `.env.example`, not `.env.local.example`. No local `.env` or
`.env.local` file was present at inspection. There is no compatibility alias for
the old flag. Normal `npm run dev` still enables the local rewrite automatically;
the explicit flag is for local production builds. `TULYA_PREVIEW_URL`, draft
storage keys and the request logger name are outside this requested rename.

The complete path audit, including exact candidate replacement lines for all
three tracked files containing old absolute paths, is in
[rebrand-gate-3-path-inventory.md](rebrand-gate-3-path-inventory.md). Those tracked
occurrences record historical execution locations and are preserved as evidence.
There are no active source/config/editor absolute-path replacements to apply.

## Evidence for Python setup

- `README.md:18–21` documents a separate `.tools/bootstrap` environment containing
  uv 0.12.19; CI also installs that exact uv version with pip.
- The existing `.venv/Scripts` contains `uv.exe`, `uvx.exe` and `uvw.exe`.
- `.venv/Lib/site-packages/uv-0.12.19.dist-info/INSTALLER` contains `pip`, and its
  `RECORD` lists those executables. This is a pip installation, not evidence of
  an undocumented manual executable copy.
- The existing `.venv` also contains pip 23.2.1. No checked-in script documents an
  earlier `ensurepip` invocation. The commands below use `ensurepip` to restore
  that existing pip capability, then reinstall uv 0.12.19 after the locked sync.
- `.venv/pyvenv.cfg` currently has `prompt = tulya`; the replacement gets
  `prompt = augmentr`. The installed project distribution becomes `augmentr`.

## Manual move and environment recreation

Save your work, stop the development/test servers, and close IDE/Codex windows
and terminals using this checkout. Copy this plan outside the workspace first.
Run the following in a fresh, **non-activated PowerShell** window from the parent
directory. Do not run it through a terminal whose host keeps this checkout open.
Review each section before running it. If a move fails because of a lock, stop,
close the locking process yourself, and inspect both paths before retrying.
The commands do not kill processes or merge into an existing destination.

```powershell
$ErrorActionPreference = 'Stop'
$source = 'C:\Users\Advaet\Documents\Projects\TULYA'
$target = 'C:\Users\Advaet\Documents\Projects\AUGMENTR'
$parent = 'C:\Users\Advaet\Documents\Projects'
$basePython = 'C:\Program Files\Python312\python.exe'

Set-Location -LiteralPath $parent
if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw 'Expected source directory does not exist. Inspect the paths before continuing.'
}
if (Test-Path -LiteralPath $target) {
    throw 'Destination already exists. Stop; do not merge or overwrite it.'
}
$sourceItem = Get-Item -LiteralPath $source -Force
if ($sourceItem.FullName -ine $source -or
    ($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'Source must be the exact ordinary directory shown above.'
}
if (-not (Test-Path -LiteralPath $basePython -PathType Leaf)) {
    throw 'The inspected Python 3.12 interpreter is missing.'
}
$bootstrapUv = Join-Path $source '.tools\bootstrap\Scripts\uv.exe'
if (-not (Test-Path -LiteralPath $bootstrapUv -PathType Leaf)) {
    throw 'The existing bootstrap uv executable is missing.'
}
$uvVersion = & $bootstrapUv --version
if ($LASTEXITCODE -ne 0 -or $uvVersion -notmatch '^uv 0\.12\.19(?:\s|$)') {
    throw 'Expected the existing uv 0.12.19 executable.'
}
$lockHash = (Get-FileHash -LiteralPath (Join-Path $source 'uv.lock') -Algorithm SHA256).Hash

# Move only after you have closed all processes holding this directory.
Move-Item -LiteralPath $source -Destination $target -ErrorAction Stop
if (Test-Path -LiteralPath $source) { throw 'Source still exists; inspect the move.' }
if ((Get-Item -LiteralPath $target -Force).FullName -ine $target) {
    throw 'Unexpected destination after move.'
}
Set-Location -LiteralPath $target

# Use the existing standalone uv executable outside the environment being removed.
$bootstrapUv = Join-Path $target '.tools\bootstrap\Scripts\uv.exe'
$env:Path = "$target\.tools\bootstrap\Scripts;$target\.tools\node-v22.23.3-win-x64;$env:Path"
$env:UV_CACHE_DIR = Join-Path $target '.tools\uv-cache'
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $target '.tools\browsers'
Remove-Item Env:VIRTUAL_ENV, Env:UV_PROJECT_ENVIRONMENT -ErrorAction SilentlyContinue
Remove-Item Env:TULYA_LOCAL_API_PROXY -ErrorAction SilentlyContinue

# Delete only these verified paths inside the renamed checkout.
# .next and tsconfig.tsbuildinfo are generated caches containing old build paths.
foreach ($relative in @('.venv', '.next', 'tsconfig.tsbuildinfo')) {
    $candidate = [IO.Path]::GetFullPath((Join-Path $target $relative))
    if (-not $candidate.StartsWith($target + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing deletion outside the new workspace: $candidate"
    }
    if (Test-Path -LiteralPath $candidate) {
        $item = Get-Item -LiteralPath $candidate -Force
        if ($item.FullName -ine $candidate -or
            ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Refusing an unexpected or linked deletion target: $candidate"
        }
        Remove-Item -LiteralPath $candidate -Recurse -Force -ErrorAction Stop
    }
}

& $bootstrapUv venv --prompt augmentr --python $basePython .venv
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
& $bootstrapUv sync --locked --python $basePython
if ($LASTEXITCODE -ne 0) { throw 'Locked dependency installation failed.' }
if ((Get-FileHash -LiteralPath (Join-Path $target 'uv.lock') -Algorithm SHA256).Hash -ne $lockHash) {
    throw 'uv.lock changed unexpectedly. Stop and inspect it.'
}

# Restore the pip and uv tools that were present in the old environment.
# Do this AFTER exact sync, which removes packages outside uv.lock.
$venvPython = Join-Path $target '.venv\Scripts\python.exe'
& $venvPython -m ensurepip
if ($LASTEXITCODE -ne 0) { throw 'pip bootstrap failed.' }
& $venvPython -m pip install 'uv==0.12.19'
if ($LASTEXITCODE -ne 0) { throw 'uv installation inside .venv failed.' }
& (Join-Path $target '.venv\Scripts\uv.exe') --version
if ($LASTEXITCODE -ne 0) { throw 'The restored uv executable failed.' }
& $venvPython -c "import importlib.metadata, pathlib, sys; assert pathlib.Path(sys.prefix).resolve() == pathlib.Path('.venv').resolve(); assert importlib.metadata.version('augmentr') == '0.1.0'; print(sys.executable); print('augmentr', importlib.metadata.version('augmentr'))"
if ($LASTEXITCODE -ne 0) { throw 'The relocated Python environment failed verification.' }
Select-String -LiteralPath '.venv\pyvenv.cfg' -Pattern '^prompt = augmentr$'
```

`uv sync --locked` installs the exact locked project/development dependency set
and refuses to rewrite the lock. pip and uv are restored afterward as local
maintenance tools, matching the prior setup; they are not new project dependencies.
A later exact `uv sync` can remove these two extras again. Keep the bootstrap
uv first on PATH so synchronization does not depend on an executable inside
the environment being synchronized. If needed, repeat the two tool-restoration
commands after a later exact sync. Ordinary `uv run` uses inexact synchronization.

Do not activate the moved `.tools/bootstrap` or `.tools/gate-2-env` environments:
their generated activation/editable files retain old paths. Only the standalone
bootstrap `uv.exe` is used above; the rebuilt `.venv` is the application environment.
Do not use the old `.tools/release-check` snapshot as the active checkout.
Reopen your IDE/Codex project at `AUGMENTR` and select
`AUGMENTR\.venv\Scripts\python.exe` as the interpreter.

## Manual development checks

Run this setup in each new test/development PowerShell window:

```powershell
Set-Location -LiteralPath 'C:\Users\Advaet\Documents\Projects\AUGMENTR'
$env:Path = "$PWD\.tools\bootstrap\Scripts;$PWD\.tools\node-v22.23.3-win-x64;$env:Path"
$env:UV_CACHE_DIR = "$PWD\.tools\uv-cache"
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\.tools\browsers"
Remove-Item Env:VIRTUAL_ENV, Env:UV_PROJECT_ENVIRONMENT -ErrorAction SilentlyContinue
Remove-Item Env:TULYA_LOCAL_API_PROXY -ErrorAction SilentlyContinue
```

Terminal 1:

```powershell
npm run dev:api
```

Terminal 2:

```powershell
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Terminal 3, after both servers are ready:

```powershell
$backend = Invoke-RestMethod 'http://127.0.0.1:18000/api/health'
$proxied = Invoke-RestMethod 'http://127.0.0.1:3000/api/health'
if ($backend.status -ne 'ok' -or $proxied.status -ne 'ok') {
    throw 'Backend or frontend proxy health failed.'
}
$schema = Invoke-RestMethod 'http://127.0.0.1:3000/api/openapi.json'
if ($schema.info.title -ne 'Augmentr API') { throw 'Unexpected backend API title.' }
'Backend and frontend proxy health passed.'
```

Check `/solve` in the browser and analyze/solve a preset. If the old proxy flag
was configured outside this repo (for example in a personal PowerShell profile
or Windows environment settings), replace it there with
`AUGMENTR_LOCAL_API_PROXY`; no external profile or persistent environment was
inspected or changed. No production/Vercel environment flag should be added.

## Owner-run full verification

After checking development mode, stop both servers yourself, use the setup above
in a fresh PowerShell window, and run the following from `AUGMENTR`. Native-command
failures stop the sequence so the final status cannot hide an earlier failure.

```powershell
$ErrorActionPreference = 'Stop'
foreach ($script in @('lint:python', 'typecheck:python', 'test:python', 'contracts:check', 'audit:runtime')) {
    npm run $script
    if ($LASTEXITCODE -ne 0) { throw "$script failed." }
}
$env:AUGMENTR_LOCAL_API_PROXY = '1'
npm run check
if ($LASTEXITCODE -ne 0) { throw 'Frontend lint, types, unit tests or production build failed.' }
$env:E2E_PRODUCTION = '1'
$env:E2E_REUSE_SERVERS = '0'
npm run test:e2e
if ($LASTEXITCODE -ne 0) { throw 'Playwright/accessibility verification failed.' }
Remove-Item Env:AUGMENTR_LOCAL_API_PROXY, Env:E2E_PRODUCTION, Env:E2E_REUSE_SERVERS
Get-FileHash -LiteralPath 'uv.lock' -Algorithm SHA256
git status --short
```

Expected baseline: 447 pytest tests, 130 Vitest tests and 46 desktop/mobile
Playwright tests, with zero axe violations. These are the Gate 2 baseline, not
claimed Gate 3 results. Expected `uv.lock` SHA-256:
`9c26af0371256de7cb7e9440aa3fe4816dd8c8113d07e6967aa3c37d8603207a`.

Next.js may regenerate `next-env.d.ts` import paths during the build; inspect
that generated diff separately from the rebrand changes. No commit, push or
remote operation is included in this command plan. Report the new working path,
development/proxy results and full-suite counts before the Gate 3 completion
report is written. Gate 4 remains blocked on your explicit approval.
