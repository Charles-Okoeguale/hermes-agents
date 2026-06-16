import json
import re
from datetime import datetime
from pathlib import Path


def save_article(args: dict, **kwargs) -> str:
    title = args.get("title", "article").strip()
    content = args.get("content", "").strip()
    if not content:
        return json.dumps({"error": "No content provided"})

    safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")[:60]
    date = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{date}_{safe_title}.md"

    output_dir = Path(__file__).resolve().parents[3] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    out_path = output_dir / filename
    out_path.write_text(f"# {title}\n\n{content}\n")
    return json.dumps({"saved": True, "path": str(out_path), "filename": filename})
