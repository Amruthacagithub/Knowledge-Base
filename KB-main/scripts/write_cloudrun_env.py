"""Write Cloud Run env-vars YAML from project/.env (gitignored output)."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import dotenv_values

KEYS = [
    "DATABASE_URL",
    "QDRANT_URL",
    "QDRANT_API_KEY",
    "GEMINI_API_KEY",
    "GEMINI_API_KEY_2",
    "GEMINI_API_KEY_3",
    "GEMINI_MODEL",
    "GEMINI_MODEL_FALLBACK",
    "JWT_SECRET",
    "CORS_ORIGINS",
    "QDRANT_COLLECTION",
]

def main():
    env = dotenv_values(PROJECT_ROOT / ".env")
    out = PROJECT_ROOT / "deploy" / "cloudrun.env.yaml"
    out.parent.mkdir(exist_ok=True)

    lines = []
    for key in KEYS:
        val = (env.get(key) or "").strip()
        if not val and key == "JWT_SECRET":
            val = "ekip-prod-change-me"
        if not val and key == "CORS_ORIGINS":
            val = "http://localhost:5173,https://localhost:5173"
        if val:
            escaped = val.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(lines)} vars)")


if __name__ == "__main__":
    main()
