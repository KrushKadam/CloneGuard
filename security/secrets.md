# CloneGuard — Secrets Policy

## GNANI_API_KEY Handling

| Rule | Detail |
|---|---|
| **Storage** | Environment variable only (`GNANI_API_KEY`). Never in files. |
| **Transport** | Sent in `X-API-Key-ID` header over HTTPS to `api.vachana.ai`. |
| **Logging** | Never printed. `api_key_present()` returns boolean only (`app.py:66`). |
| **Git** | Never committed. `.gitignore` excludes `.env`. History scan found only placeholder `your-key-here`. |

## How to Set the Key

**Preferred (persistent, no shell history):**
1. Windows Start → "Edit the system environment variables"
2. Environment Variables → User variables → New
3. Name: `GNANI_API_KEY`, Value: *your key from app.gnani.ai*
4. Click OK on all dialogs
5. **Restart terminal / VS Code** so the new variable is picked up

**Terminal (works but leaves key in shell history):**
```powershell
$env:GNANI_API_KEY = "your-actual-key-here"
```
> ⚠️ PowerShell history (`Get-History`, `%USERPROFILE%\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt`) will contain the key. Use the system env var method instead.

## Verify Before Push

Run these checks before every `git push`:

```bash
# 1. No .env or key files staged
git status --short

# 2. Search working tree for key-shaped strings
grep -rE "(cfut_|cfat_|GNANI_API_KEY\s*=\s*\S{20,})" --include="*.py" --include="*.md" --include="*.txt" --include="*.json" .

# 3. Search git history (all branches)
git log -p --all | grep -iE "(cfut_|cfat_|GNANI_API_KEY\s*=\s*\S{20,})"
```

Expected output: **zero matches** (or only the placeholder `your-key-here` in README).

## Rotation Procedure (If Leaked)

1. Go to **app.gnani.ai** → Usage / API Keys
2. Revoke the compromised key
3. Generate a new key
4. Update the system environment variable (same steps as "How to Set")
5. Restart terminal / VS Code
6. Verify `api_key_present()` shows success in the app sidebar

## Audit Evidence (2026-11-09)

- Zero real secrets in working tree
- Zero real secrets in git history (all commits scanned)
- Only placeholder `your-key-here` found in `README.md` line 67
- Key never logged by application code (boolean check only)

---
*Secrets policy documented 9 November 2026. Matches code at commits `1cdeb5a`, `8d0deb6`.*