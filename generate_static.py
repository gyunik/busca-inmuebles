import os
from pathlib import Path

static_dir = Path("backend/app/static")
static_dir.mkdir(parents=True, exist_ok=True)

# Read or generate html
html_path = static_dir / "index.html"
print(f"Target path: {html_path.resolve()}")
