param(
  [string]$ArduinoCli = "arduino-cli",
  [string]$ConfigFile = "",
  [string]$Output = "",
  [string]$Python = "python"
)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
& $Python (Join-Path $PSScriptRoot "prepare_firmware.py")
if ($LASTEXITCODE -ne 0) { throw "Sketch preparation failed; upstream review or local edits require attention." }
if (!$Output) { $Output = Join-Path $projectRoot "output/firmware" }
$buildPath = Join-Path $Output "_build"
$cliArgs = @()
if ($ConfigFile) { $cliArgs += @("--config-file", $ConfigFile) }
$cliArgs += @("compile","--fqbn","esp32:esp32:esp32s3:CDCOnBoot=cdc,PSRAM=enabled,PartitionScheme=min_spiffs",
  "--library",(Join-Path $projectRoot "vendor/Adafruit_NeoPixel"),"--output-dir",$Output,"--build-path",$buildPath,
  (Join-Path $projectRoot "firmware/HeishaMon"))
& $ArduinoCli @cliArgs
if ($LASTEXITCODE -ne 0) { throw "ESP32-S3 build failed; no release package created." }
$sourceBin = Join-Path $Output "HeishaMon.ino.bin"
if (!(Test-Path -LiteralPath $sourceBin)) { throw "Application binary missing" }
if ((Get-Item -LiteralPath $sourceBin).Length -gt 0x1df000) { throw "Application exceeds web-OTA limit for min_spiffs" }
$md5 = (Get-FileHash -LiteralPath $sourceBin -Algorithm MD5).Hash.ToLowerInvariant()
$targetBin = Join-Path $Output "HeishaMon_ESP32-HMX-0.1.0-dev.7-$md5.bin"
Copy-Item -LiteralPath $sourceBin -Destination $targetBin
$sha = (Get-FileHash -LiteralPath $targetBin -Algorithm SHA256).Hash.ToLowerInvariant()
$installed = Get-Content -Raw (Join-Path $projectRoot 'firmware/hmx-installed.json') | ConvertFrom-Json
$sourceHashes = @{}
foreach ($entry in $installed.installed_sha256.PSObject.Properties) {
  $sourcePath = Join-Path (Join-Path $projectRoot 'firmware') $entry.Name
  $sourceHashes[$entry.Name] = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
}
$optionsPath = Join-Path $buildPath 'build.options.json'
$coreVersion = 'not recorded'
if (Test-Path -LiteralPath $optionsPath) {
  $options = Get-Content -Raw $optionsPath | ConvertFrom-Json
  $corePath = ($options.hardwareFolders -split ',')[0]
  if ($corePath) { $coreVersion = Split-Path -Leaf $corePath }
}
$manifest = [ordered]@{
  image=(Split-Path -Leaf $targetBin);size=(Get-Item -LiteralPath $targetBin).Length
  md5=$md5;sha256=$sha;target='ESP32-S3';partition='min_spiffs'
  upstream=$installed.baseline;extension=$installed.extension;hardware_tested=$false
  installed_sha256=$sourceHashes
  build_environment=@{core=$coreVersion;method='Arduino CLI';time_utc=[DateTime]::UtcNow.ToString('o')}
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 (Join-Path $Output 'firmware_manifest.json')

Get-FileHash -LiteralPath $targetBin -Algorithm SHA256 | Format-List
Write-Host "Web-Update: $targetBin"
Write-Host "Upload only the application .bin, never the merged or bootloader image."
