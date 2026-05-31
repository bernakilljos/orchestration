param([string[]]$Files)
foreach ($f in $Files) {
    if (-not (Test-Path $f)) { Write-Warning "missing: $f"; continue }
    $bytes = [System.IO.File]::ReadAllBytes($f)
    $text = [System.Text.Encoding]::UTF8.GetString($bytes)
    # Strip BOM if present
    if ($text.StartsWith([char]0xFEFF)) { $text = $text.Substring(1) }
    # LF -> CRLF (preserve existing CRLF)
    $fixed = [regex]::Replace($text, "(?<!`r)`n", "`r`n")
    if ($fixed -ne $text) {
        [System.IO.File]::WriteAllText($f, $fixed, (New-Object System.Text.UTF8Encoding($false)))
        Write-Output "fixed: $f"
    } else {
        Write-Output "ok:    $f"
    }
}
