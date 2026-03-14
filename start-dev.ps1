$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$backendArgs = @(
  "-NoExit",
  "-Command",
  "Set-Location '$projectRoot'; python run.py"
)

$devmentorArgs = @(
  "-NoExit",
  "-Command",
  "Set-Location '$projectRoot\\devmentor'; npm.cmd run dev"
)

Start-Process powershell -ArgumentList $backendArgs
Start-Process powershell -ArgumentList $devmentorArgs
