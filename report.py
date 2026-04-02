import os
from datetime import date, datetime, timedelta

from jinja2 import Environment, FileSystemLoader

from models import Paper

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def generate_html(
    keywords: list[str],
    peer_reviewed: list[Paper],
    preprints: list[Paper],
    output_path: str,
) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("report.html")

    today = date.today()
    start = today - timedelta(days=30)
    date_range = f"{start.isoformat()} to {today.isoformat()}"
    total_count = len(peer_reviewed) + len(preprints)

    html = template.render(
        keywords=keywords,
        date_range=date_range,
        total_count=total_count,
        peer_reviewed=peer_reviewed,
        preprints=preprints,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path
