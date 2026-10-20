# TokenPulse zero-key demo: synthetic data + API + dashboard. No API keys required.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "==> [1/4] Backend deps (uv sync)"
Push-Location backend; uv sync --extra dev; Pop-Location

Write-Host "==> [2/4] Seed synthetic dataset (demo mode, no keys)"
Push-Location backend
uv run tokenpulse --config tokenpulse.demo.toml seed --reset
# TODO(US3 T067): add `uv run tokenpulse report` here once the report command lands.
Pop-Location

Write-Host "==> [3/4] Start API on http://127.0.0.1:8000"
$api = Start-Process -PassThru -NoNewWindow -WorkingDirectory "$root/backend" `
  -FilePath "uv" -ArgumentList "run", "tokenpulse", "--config", "tokenpulse.demo.toml", "serve", "--host", "127.0.0.1", "--port", "8000"

try {
  Write-Host "==> [4/4] Start dashboard on http://localhost:5173"
  if (Get-Command npm -ErrorAction SilentlyContinue) {
    Push-Location frontend; npm ci; npm run dev; Pop-Location
  } else {
    Write-Host "npm not found - install Node 20+ to run the dashboard. API is up at :8000."
    Wait-Process -Id $api.Id
  }
} finally {
  if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id -Force }
}
