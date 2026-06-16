import json
import os
import re


def save_note(args: dict, **kwargs) -> str:
    title = (args.get("title") or "").strip()
    body = args.get("body") or ""
    if not title:
        return json.dumps({"error": "No title provided"})

    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", title).strip("_") or "note"
    os.makedirs("notes", exist_ok=True)
    path = os.path.join("notes", f"{safe}.md")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{body}\n")
        return json.dumps({"success": True, "saved": path})
    except Exception as e:
        return json.dumps({"error": f"Save failed: {e}"})
