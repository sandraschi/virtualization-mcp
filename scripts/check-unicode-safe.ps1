# Check for non-ASCII dashes/smart-quotes in source files that could break parsers
# Exits 1 if any found (blocks commit), 0 if clean.

$bad = @()
$srcDirs = @('src','webapp/backend','webapp/frontend/src','assets','tests','scripts')
$extensions = @('.py','.ps1','.cmd','.bat','.ts','.tsx','.js','.jsx','.md')
$badChars = @(
    @{Char=[char]0x2013; Name='EN DASH'},
    @{Char=[char]0x2014; Name='EM DASH'},
    @{Char=[char]0x2018; Name='LEFT SINGLE QUOTE'},
    @{Char=[char]0x2019; Name='RIGHT SINGLE QUOTE'},
    @{Char=[char]0x201C; Name='LEFT DOUBLE QUOTE'},
    @{Char=[char]0x201D; Name='RIGHT DOUBLE QUOTE'}
)

foreach ($dir in $srcDirs) {
    if (-not (Test-Path $dir)) { continue }
    Get-ChildItem -Path $dir -Recurse -File -Include @($extensions | ForEach-Object { "*$_" }) | ForEach-Object {
        $content = Get-Content -Path $_.FullName -Raw -ErrorAction SilentlyContinue
        if (-not $content) { return }
        $lines = $content -split "`n"
        for ($i = 0; $i -lt $lines.Count; $i++) {
            foreach ($bc in $badChars) {
                $idx = $lines[$i].IndexOf($bc.Char)
                if ($idx -ge 0) {
                    $context = $lines[$i].Substring([Math]::Max(0,$idx-10), [Math]::Min(30, $lines[$i].Length-$idx+10)).Trim()
                    $bad += "  $($_.FullName):$($i+1):$idx $($bc.Name) (U+$([int]$bc.Char).ToString('X4')) ...$context..."
                }
            }
        }
    }
}

if ($bad.Count -gt 0) {
    Write-Host "UNICODE SAFETY: $($bad.Count) non-ASCII dash/quote characters found:" -ForegroundColor Red
    $bad | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
    exit 1
} else {
    Write-Host "UNICODE SAFETY: Clean" -ForegroundColor Green
    exit 0
}
