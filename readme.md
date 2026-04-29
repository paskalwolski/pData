# pData

An Assetto Corsa Python app that captures per-metre telemetry during a session and uploads it to a cloud API for storage and analysis.

---

## Installation

### Option 1 — Release zip (recommended for users)

1. Download `pData.zip` from the [Releases](../../releases) page
2. Drag the zip into Content Manager — it will extract to the correct location automatically

### Option 2 — Source (recommended for developers)

Clone this repo directly into your AC Python apps folder:

```
assettocorsa/apps/python/pData/
```

---

## Cutting a release

1. Commit and push all changes to `main`
2. Create and push an annotated tag:
   ```
   git tag -a v1.0.0 -m "Release notes here"
   git push origin v1.0.0
   ```
3. GitHub Actions builds `pData.zip` and attaches it to a new release automatically
