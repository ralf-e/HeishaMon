param([switch]$PurgeTemporary)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path.TrimEnd('\')
$archiveRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'archive/previous-revisions'))
function Assert-InProject([string]$value) {
  $absolute = [IO.Path]::GetFullPath($value)
  if (!$absolute.StartsWith($projectRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {throw "Outside project: $absolute"}
  return $absolute
}
$null = Assert-InProject $archiveRoot
New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null
$moved = [Collections.Generic.List[string]]::new()
function Move-Archived([string]$source,[string]$category) {
  if (!(Test-Path -LiteralPath $source)) {return}
  $resolved = (Resolve-Path -LiteralPath $source).Path
  $null = Assert-InProject $resolved
  $destinationFolder = Assert-InProject (Join-Path $archiveRoot $category)
  New-Item -ItemType Directory -Path $destinationFolder -Force | Out-Null
  $destination = Assert-InProject (Join-Path $destinationFolder (Split-Path -Leaf $resolved))
  if (Test-Path -LiteralPath $destination) {
    $baseName = [IO.Path]::GetFileNameWithoutExtension($destination)
    $extensionName = [IO.Path]::GetExtension($destination)
    $index = 1
    do {$destination = Assert-InProject (Join-Path $destinationFolder ($baseName + '.' + $index + $extensionName)); $index++} while (Test-Path -LiteralPath $destination)
  }
  Move-Item -LiteralPath $resolved -Destination $destination
  $moved.Add($resolved.Substring($projectRoot.Length+1))
}
Move-Archived (Join-Path $projectRoot 'manufacturing/JLCPCB/Rev05') 'manufacturing'
$keepOutput = @('HeishaMon_V6_Touch_Anleitung_dev7_Rev06.pdf','HeishaMon_V6_Touch_Anleitung_dev7_Rev06.md','HeishaMon_V6_Touch_Projekt_dev7_Rev06.zip','HeishaMon_V6_KiCad_Rev06.zip','HeishaMon_V6_JLCPCB_Rev06.zip','HeishaMon_V6_Schaltplan_Rev06.pdf','current-release.json','BOM_HeishaMon_V6_Rev06.csv','CPL_HeishaMon_V6_Rev06.csv','Gerber_HeishaMon_V6_Rev06.zip')
Get-ChildItem -LiteralPath (Join-Path $projectRoot 'output') -File | Where-Object {$_.Name -notin $keepOutput} | ForEach-Object {Move-Archived $_.FullName 'output'}
Get-ChildItem -LiteralPath (Join-Path $projectRoot 'hardware') | Where-Object {$_.Name -match '^Platzierung|^Gesamtschaltplan(?:_rev02.*|_rev0[345])?\.pdf$|^Gesamtverdrahtung_rev0[2345]\.pdf$|\.kicad_prl$|-backups$'} | ForEach-Object {Move-Archived $_.FullName 'hardware'}
foreach ($name in @('Montageanschluesse_rev05.png','Display_Hochformat_Entwurf.png','Display_Quer_6x8_Original.png','Display_Quer_6x8_Vorschau.png','Gesamtschaltplan_final.png','Gesamtschaltplan_rev02.png','Gesamtverdrahtung_rev02.png','Platzierung_final.png','Platzierung_rev02.png')) {Move-Archived (Join-Path $projectRoot "docs/$name") 'docs'}
foreach ($name in @('portrait_preview.py','preview_landscape_6x8.py','arduino-cli.yaml')) {Move-Archived (Join-Path $projectRoot "tools/$name") 'tools'}
Move-Archived (Join-Path $projectRoot 'write_probe.txt') 'scratch'
$reference = Join-Path $projectRoot 'HeishaMon_Funktion_Aufbau_Benutzung_2026.pdf'
if (Test-Path -LiteralPath $reference) {
  $referenceFolder = Assert-InProject (Join-Path $projectRoot 'docs/reference')
  New-Item -ItemType Directory -Path $referenceFolder -Force | Out-Null
  $destination = Assert-InProject (Join-Path $referenceFolder (Split-Path -Leaf $reference))
  Move-Item -LiteralPath $reference -Destination $destination
}
if ($PurgeTemporary) {
  $temporary = (Resolve-Path -LiteralPath (Join-Path $projectRoot 'tmp')).Path
  $null = Assert-InProject $temporary
  if ((Split-Path -Leaf $temporary) -ne 'tmp') {throw 'Refusing non-tmp cleanup'}
  if ((Get-Item -LiteralPath $temporary).Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'Refusing tmp reparse point'}
  Remove-Item -LiteralPath $temporary -Recurse -Force
  New-Item -ItemType Directory -Path $temporary | Out-Null
  Set-Content -LiteralPath (Join-Path $temporary 'README.md') -Value 'Generated temporary files only. Current deliverables are in output/. Safe to clear after validation.' -Encoding utf8
}
foreach ($folder in @('tools/__pycache__','tests/__pycache__')) {
  $cache = Join-Path $projectRoot $folder
  if (Test-Path -LiteralPath $cache) {
    $resolved = (Resolve-Path -LiteralPath $cache).Path
    $null = Assert-InProject $resolved
    if ((Split-Path -Leaf $resolved) -ne '__pycache__') {throw 'Unexpected cache path'}
    Remove-Item -LiteralPath $resolved -Recurse -Force
  }
}
$result = @{archived_items=$moved;temporary_purged=[bool]$PurgeTemporary;current_output=$keepOutput}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $projectRoot 'validation/cleanup_status.json') -Encoding utf8
$result | ConvertTo-Json -Depth 5
