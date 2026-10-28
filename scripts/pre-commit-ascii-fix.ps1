# Fleet: auto-normalize confusable Unicode to ASCII in PowerShell files.
# Template copy lives at mcp-central-docs/templates/pre-commit-ascii-fix.ps1 -
# vendor it to {repo}/scripts/ and keep the vendor copy in sync.
#
# Runs BEFORE the ps1-ascii-only fail-hook: this fixes the known-dangerous
# characters (em/en dashes, smart quotes, ellipsis, non-breaking space) that
# PS 5.1 misdecodes when a BOM is absent; anything else non-ASCII still fails
# the gate so genuinely foreign text (e.g. an already-mojibake FFFD) stays
# visible instead of being silently masked.
#
# Autofix convention (same as end-of-file-fixer): modifies files in place and
# exits 1 when anything changed, so the commit aborts and the user re-stages
# with the fix included. Never exits 0 after modifying (the staged blob would
# otherwise commit the UNFIXED content).
# ASCII only in this file by definition - it must pass the very gate it feeds.

$ErrorActionPreference = "Stop"

$map = [ordered]@{
    ([char]0x2014) = "-"   # EM DASH
    ([char]0x2013) = "-"   # EN DASH
    ([char]0x2018) = "'"   # LEFT SINGLE QUOTATION MARK
    ([char]0x2019) = "'"   # RIGHT SINGLE QUOTATION MARK
    ([char]0x201C) = '"'   # LEFT DOUBLE QUOTATION MARK
    ([char]0x201D) = '"'   # RIGHT DOUBLE QUOTATION MARK
    ([char]0x2026) = "..." # HORIZONTAL ELLIPSIS
    ([char]0x00A0) = " "   # NO-BREAK SPACE (invisible, breaks tokens)
}

$changed = $false
foreach ($path in $args) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
    $raw = [System.IO.File]::ReadAllBytes($path)
    $hasBom = ($raw.Length -ge 3 -and $raw[0] -eq 0xEF -and $raw[1] -eq 0xBB -and $raw[2] -eq 0xBF)
    if ($hasBom -and $raw.Length -eq 3) {
        $body = [byte[]]@()
    } elseif ($hasBom) {
        $body = $raw[3..($raw.Length - 1)]
    } else {
        $body = $raw
    }
    $body = [byte[]]$body
    $text = [System.Text.Encoding]::UTF8.GetString($body)
    $fixed = $text
    foreach ($entry in $map.GetEnumerator()) {
        # Explicit ToString on both sides: String.Replace has (char,char)
        # and (string,string) overloads, and overload resolution picks the
        # char form for single-char values but throws for multi-char ones
        # (ellipsis). Forcing strings makes every entry deterministic.
        $fixed = $fixed.Replace($entry.Key.ToString(), $entry.Value)
    }
    if ($fixed -ceq $text) { continue }
    $out = [System.Text.Encoding]::UTF8.GetBytes($fixed)
    if ($hasBom) { $out = ([byte[]]@(0xEF, 0xBB, 0xBF)) + $out }
    [System.IO.File]::WriteAllBytes($path, $out)
    Write-Host "ascii-fix: normalized $($path)"
    $changed = $true
}

if ($changed) {
    Write-Host "ascii-fix: files were modified - re-stage and commit again."
    exit 1
}
exit 0
