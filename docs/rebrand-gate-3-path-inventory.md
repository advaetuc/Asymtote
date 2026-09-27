# Gate 3 — old absolute path inventory

Snapshot taken 2026-09-27 before creating the Gate 3 instruction documents.

This is a relocation audit, not a completion report. No folder/environment was moved or recreated.

## Maintained files and exact replacement candidates

A case-insensitive search included hidden and ignored editor/config/script files.
`.vscode/settings.json` contains only the environment-manager setting; it has no absolute path. No dev script, active config, `.env.example`, or personal local env file in this checkout contains the old absolute root.

The three tracked matches below are historical records. Their exact candidate replacement lines are listed as requested, but **have not been applied**: changing a prior execution location in archived test results would make the evidence inaccurate. Relocation requires no edit to them. New test results will record the new directory.

### `docs/phase-0-report.md`

Line 3; exact proposed replacement (retain the original historical record):

```markdown
Completed locally on 2026-09-25 in `C:/Users/Advaet/Documents/Projects/AUGMENTR`.
```

### `docs/preview-verification/browser-observability-results.json`

Line 4; exact proposed replacement (retain the original historical record):

```json
      "C:\\Users\\Advaet\\Documents\\Projects\\AUGMENTR\\.tools\\node-v22.23.3-win-x64\\node.exe",
```

Line 5; exact proposed replacement (retain the original historical record):

```json
      "C:\\Users\\Advaet\\Documents\\Projects\\AUGMENTR\\node_modules\\@playwright\\test\\cli.js",
```

Line 10; exact proposed replacement (retain the original historical record):

```json
    "configFile": "C:\\Users\\Advaet\\Documents\\Projects\\AUGMENTR\\playwright.preview.config.ts",
```

Line 11; exact proposed replacement (retain the original historical record):

```json
    "rootDir": "C:/Users/Advaet/Documents/Projects/AUGMENTR/tests",
```

Line 27; exact proposed replacement (retain the original historical record):

```json
        "outputDir": "C:/Users/Advaet/Documents/Projects/AUGMENTR/test-results/preview",
```

Line 35; exact proposed replacement (retain the original historical record):

```json
        "testDir": "C:/Users/Advaet/Documents/Projects/AUGMENTR/tests",
```

Line 44; exact proposed replacement (retain the original historical record):

```json
        "outputDir": "C:/Users/Advaet/Documents/Projects/AUGMENTR/test-results/preview",
```

Line 52; exact proposed replacement (retain the original historical record):

```json
        "testDir": "C:/Users/Advaet/Documents/Projects/AUGMENTR/tests",
```

### `docs/preview-verification/browser-results.json`

Line 4; exact proposed replacement (retain the original historical record):

```json
      "C:\\Users\\Advaet\\Documents\\Projects\\AUGMENTR\\.tools\\node-v22.23.3-win-x64\\node.exe",
```

Line 5; exact proposed replacement (retain the original historical record):

```json
      "C:\\Users\\Advaet\\Documents\\Projects\\AUGMENTR\\node_modules\\@playwright\\test\\cli.js",
```

Line 9; exact proposed replacement (retain the original historical record):

```json
    "configFile": "C:\\Users\\Advaet\\Documents\\Projects\\AUGMENTR\\playwright.preview.config.ts",
```

Line 10; exact proposed replacement (retain the original historical record):

```json
    "rootDir": "C:/Users/Advaet/Documents/Projects/AUGMENTR/tests/e2e",
```

Line 26; exact proposed replacement (retain the original historical record):

```json
        "outputDir": "C:/Users/Advaet/Documents/Projects/AUGMENTR/test-results/preview",
```

Line 34; exact proposed replacement (retain the original historical record):

```json
        "testDir": "C:/Users/Advaet/Documents/Projects/AUGMENTR/tests/e2e",
```

Line 42; exact proposed replacement (retain the original historical record):

```json
        "outputDir": "C:/Users/Advaet/Documents/Projects/AUGMENTR/test-results/preview",
```

Line 50; exact proposed replacement (retain the original historical record):

```json
        "testDir": "C:/Users/Advaet/Documents/Projects/AUGMENTR/tests/e2e",
```

## Local generated state and caches

The broader text search found **165 files**, including the three tracked files above. Every matching file is listed below. Git internals were excluded; binary executables and compiled bytecode are not source text and are regenerated rather than edited. This inventory is a snapshot; running tools may create additional cache/log matches.

Generated files are not safely fixed by substituting source lines. In particular, virtual-environment activation scripts, editable-install metadata, executable launchers and cached bundles must be recreated or left unused. The manual plan recreates `.venv` and removes `.next`/TypeScript build state. Historical logs and test evidence remain intact.

| File | Treatment |
| --- | --- |
| `.hypothesis/constants/03729dceb889d95a` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/03fc8d23f3c6d36d` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/060e211d97e94168` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/0b49aab515dfa52c` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/0cc1b0ff970ff580` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/0dd330c75cad22c0` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/0f8de46b5d3ec00a` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/0fda2695cff1592d` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/18b4929c48c29f6b` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/1b0778992fed7bfa` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/1fca23b32b07364d` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/2961e931f10449a8` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/2b30addddb24faa4` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/2bddf739352f6850` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/2de9f69efe16bcbf` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/3076f26f8a789b73` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/3144531b396ff7fc` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/33914cb39f33120c` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/3ce1c7f4e66c4804` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/3e5827b74603b80d` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/3f90b33cf19c4257` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/4661595d7e058b8a` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/483869f5ea05b450` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/494a3b0bfa0f6771` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/4c03962bc321d01d` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/4c8a12c5c69c6e29` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/587aceef7d46cee9` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/59c8798dbfeef243` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/59d18853dd0d299b` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/59fb305eec97fb2d` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/5d4d209ca76758f1` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/6047b6bc0fd922c7` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/60d5b8c7a772ac16` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/612e2f5031131c86` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/63c6a8137638c1f6` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/6cec64810eecdc91` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/6d8cb675578b44fb` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/7b8aa9a1225a7bdb` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/88d90638fd1a312a` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/8d6785f849b489e2` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/93515f541a31400d` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/97c38cc225e61eb8` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/a067a5b22eef97e6` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/a154e43f9e61e7be` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/a67db699e173f78b` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/ad8b5744ad901af6` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/c19ca1f093976718` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/c4599169ec150bfb` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/caf9528345da6a04` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/cf4fed711aa2a02f` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/d1628731147660da` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/db7a967ed6969343` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/dd0673bea7385666` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/e1bbaf2deccd11aa` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/e74bed1e42649d26` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/ebd91e5f09bb7706` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/fb47c3c23b98c641` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/fbf806fc042a6b21` | Generated test cache; no source/config replacement needed. |
| `.hypothesis/constants/ff820fe57fe7d599` | Generated test cache; no source/config replacement needed. |
| `.next/dev/server/chunks/[root-of-the-server]__06ua_9v._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/node_modules_next_0zy6_dr._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/[root-of-the-server]__0713gdr._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/[root-of-the-server]__0p4ofha._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/[root-of-the-server]__0pdzyj8._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/[root-of-the-server]__0r2q6v7._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/_0u0q4mf._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/_1-sjzim._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/_109tciv._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/app_layout_tsx_2144vk_._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/components_solver_report-preview_tsx_1_oa52w._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_01xbj_9._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_18n3ag2._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_1et2dy4._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_1f9_7tc._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_1ln3vqf._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_@swc_helpers_cjs_0s2q9hi._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_@swc_helpers_cjs__interop_require_wildcard_cjs_0t5jqoo._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_katex_dist_katex_mjs_1oxucd3._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_next_0zdrfv9._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_next_dist_0254xxt._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_next_dist_0ash3q-._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_next_dist_1un-wu7._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_next_dist_1x__ukf._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_next_dist_client_components_0wpq8j3._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_next_dist_client_components_builtin_forbidden_0symwr9.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_next_dist_client_components_builtin_global-error_0-o-goa.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_next_dist_client_components_builtin_unauthorized_0l_sp0x.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_next_dist_compiled_0d323sd._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_next_dist_esm_1ivs2qn._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_next_dist_server_route-modules_app-page_0qo_rmc._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_zod_v4_classic_1227qha._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_zod_v4_core_1354e27._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/server/chunks/ssr/node_modules_zod_v4_locales_1-qekvw._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/_1-960xk._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/_1exo0qj._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/app_globals_0yg4wg8.css.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/components_solver_geometry-plot_tsx_1ahn0z8._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/components_solver_report-preview_tsx_13_zwmf._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_1_g16xr._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_@plotly_d3_d3_0kmj3k7.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_@swc_helpers_cjs_1r9vbqw._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_culori_bundled_culori_cjs_07d5abd._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_katex_dist_katex_min_0mcg5a-.css.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_katex_dist_katex_mjs_1htj_sx._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_maplibre-gl_dist_maplibre-gl_1qepm5m.css.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_next_dist_00pwe04._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_next_dist_17-c7el._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_next_dist_1e8vcs8._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_next_dist_1qop56i._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_next_dist_20wefz_._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_next_dist_client_0_90u2t._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_next_dist_compiled_1amofcm._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_next_dist_compiled_buffer_index_18vu4gz.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_next_dist_compiled_next-devtools_index_090k2jm.js` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_next_dist_compiled_react-dom_096_9a-._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_next_dist_compiled_react-server-dom-turbopack_164kp-6._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_plotly_1nzd86l.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_plotly_js_dist_plotly-strict_min_0po2c88.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_plotly_js_src_0x5e7dv._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_plotly_js_src_components_1ct3ryk._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_plotly_js_src_lib_1y3s2ah._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_plotly_js_src_plot_api_0zh71x-._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_plotly_js_src_plots_0w_la6d._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_plotly_js_src_traces_0mq6nti._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_plotly_js_stackgl_modules_index_0ht4hrd.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_zod_v4_classic_0qgufeu._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_zod_v4_core_15b2lfp._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/dev/static/chunks/node_modules_zod_v4_locales_1-ided7._.js.map` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/required-server-files.js` | Generated build output; removed manually, rebuilt at the new path. |
| `.next/required-server-files.json` | Generated build output; removed manually, rebuilt at the new path. |
| `.tools/bootstrap/Scripts/activate` | Generated bootstrap metadata/activation; do not activate; only its standalone `uv.exe` is used. |
| `.tools/bootstrap/Scripts/activate.bat` | Generated bootstrap metadata/activation; do not activate; only its standalone `uv.exe` is used. |
| `.tools/bootstrap/pyvenv.cfg` | Generated bootstrap metadata/activation; do not activate; only its standalone `uv.exe` is used. |
| `.tools/browsers/.links/01a8c96c815b4c1c1dd0404ca3a6af9ed938d196` | Playwright-managed package link; not application config; managed by browser installation. |
| `.tools/gate-2-env/Lib/site-packages/_editable_impl_augmentr.pth` | Old test environment; do not activate or use after relocation. |
| `.tools/gate-2-env/Lib/site-packages/augmentr-0.1.0.dist-info/direct_url.json` | Old test environment; do not activate or use after relocation. |
| `.tools/gate-2-env/Scripts/activate` | Old test environment; do not activate or use after relocation. |
| `.tools/gate-2-env/Scripts/activate.bat` | Old test environment; do not activate or use after relocation. |
| `.tools/gate-2-env/Scripts/activate.csh` | Old test environment; do not activate or use after relocation. |
| `.tools/gate-2-env/Scripts/activate.fish` | Old test environment; do not activate or use after relocation. |
| `.tools/gate-2-env/Scripts/activate.nu` | Old test environment; do not activate or use after relocation. |
| `.tools/npm-cache/_logs/2026-09-25T09_59_48_489Z-debug-0.log` | Historical tool log; retain as evidence. |
| `.tools/npm-cache/_logs/2026-09-25T10_02_43_459Z-debug-0.log` | Historical tool log; retain as evidence. |
| `.tools/npm-cache/_logs/2026-09-25T10_03_36_024Z-debug-0.log` | Historical tool log; retain as evidence. |
| `.tools/rebrand-after-vitest.log` | Historical tool log; retain as evidence. |
| `.tools/rebrand-before-vitest.log` | Historical tool log; retain as evidence. |
| `.tools/rebrand-final-vitest.log` | Historical tool log; retain as evidence. |
| `.tools/rebrand-gate-2-pytest.log` | Historical tool log; retain as evidence. |
| `.tools/rebrand-gate-2-vitest.log` | Historical tool log; retain as evidence. |
| `.tools/release-check/.next/required-server-files.js` | Old release snapshot; do not use as the active checkout. |
| `.tools/release-check/.next/required-server-files.json` | Old release snapshot; do not use as the active checkout. |
| `.tools/release-check/docs/phase-0-report.md` | Old release snapshot; do not use as the active checkout. |
| `.tools/uv-cache/archive-v0/BO9TbhoisMqcYn6Z/_editable_impl_tulya.pth` | Old editable-build cache; new project path resolves a fresh editable install. |
| `.tools/uv-cache/archive-v0/D9ovIMuq9G5sQf_C/_editable_impl_augmentr.pth` | Old editable-build cache; new project path resolves a fresh editable install. |
| `.tools/uv-cache/archive-v0/Eoye6N7DaffSxVLW/_editable_impl_tulya.pth` | Old editable-build cache; new project path resolves a fresh editable install. |
| `.venv/Lib/site-packages/_editable_impl_tulya.pth` | Regenerated by deleting/recreating `.venv` and locked sync. |
| `.venv/Lib/site-packages/tulya-0.1.0.dist-info/direct_url.json` | Regenerated by deleting/recreating `.venv` and locked sync. |
| `.venv/Scripts/activate` | Regenerated by deleting/recreating `.venv` and locked sync. |
| `.venv/Scripts/activate.bat` | Regenerated by deleting/recreating `.venv` and locked sync. |
| `.venv/Scripts/activate.csh` | Regenerated by deleting/recreating `.venv` and locked sync. |
| `.venv/Scripts/activate.fish` | Regenerated by deleting/recreating `.venv` and locked sync. |
| `.venv/Scripts/activate.nu` | Regenerated by deleting/recreating `.venv` and locked sync. |
| `docs/phase-0-report.md` | Historical tracked record; exact candidates above; retain original. |
| `docs/preview-verification/browser-observability-results.json` | Historical tracked record; exact candidates above; retain original. |
| `docs/preview-verification/browser-results.json` | Historical tracked record; exact candidates above; retain original. |

For completeness, `.tools/bootstrap/pyvenv.cfg:6` has this exact **candidate** replacement:

```text
command = C:\Program Files\Python312\python.exe -m venv C:\Users\Advaet\Documents\Projects\AUGMENTR\.tools\bootstrap
```

That line records the original creation command; editing it does not make a moved environment relocatable. It is retained. Use the standalone bootstrap uv binary as documented, not its activation scripts or Python/pip launchers.

The new manual instructions intentionally mention both the old source and new destination and remove the obsolete process-level proxy variable. These are migration instructions, not leftover active references.
