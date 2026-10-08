# Troubleshooting Guide: Windows Environments

## 1. Unicode / Windows Terminal Encoding Issues

### Symptom:
`UnicodeEncodeError: 'charmap' codec can't encode character '\u2500'` or errors printing fancy box-drawing or em-dashes.

### Cause:
The legacy Windows PowerShell or Command Prompt console defaults to `cp1252` code page instead of UTF-8.

### Fix:
1. In PowerShell, enable UTF-8 mode:
   ```powershell
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   $OutputEncoding = [System.Text.Encoding]::UTF8
   ```
2. Or set the environment variable:
   ```powershell
   $env:PYTHONUTF8=1
   ```
3. In this repository, all source code and terminal printers have been hardened to use clean standard ASCII text characters (` - `, `|--`) to ensure zero crashes on any Windows terminal.

---

## 2. Windows Path Separator Issues

Always use Python's `pathlib.Path` instead of string concatenation with backslashes (`\`). Forward slashes (`/`) work natively across all Python file APIs on Windows.
