# Run tests using the project's venv and ensure `src` is importable
param(
    [Parameter(ValueFromRemainingArguments=$true)]
    $args
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$env:PYTHONPATH = $root
$pytest = Join-Path $root ".venv\Scripts\pytest.exe"

if (-Not (Test-Path $pytest)) {
    Write-Error "pytest not found at $pytest. Activate your venv or create .venv in the project root."
    exit 1
}

& $pytest @args
