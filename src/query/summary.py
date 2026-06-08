import json
from typing import Any


def summarize_results(rows: list[dict[str, Any]], limit: int = 10) -> str:
    if not rows:
        return "共 0 条记录"

    total = len(rows)
    sample = rows[:limit]
    lines = [f"共 {total} 条记录", f"展示前 {len(sample)} 条："]
    for i, row in enumerate(sample, 1):
        fields = row.get("fields", row)
        pairs = [f"{k}={v}" for k, v in fields.items()]
        lines.append(f"{i}. " + ", ".join(pairs))

    if total > limit:
        lines.append(f"... 其余 {total - limit} 条已省略")

    numeric_keys: set[str] = set()
    for row in sample:
        for k, v in row.get("fields", row).items():
            if isinstance(v, (int, float)):
                numeric_keys.add(k)

    if numeric_keys:
        lines.append("数值摘要：")
        for key in sorted(numeric_keys):
            vals = [
                float(r.get("fields", r).get(key))
                for r in rows
                if isinstance(r.get("fields", r).get(key), (int, float))
            ]
            if vals:
                lines.append(f"- {key}: 合计={sum(vals):,.2f}, 最大={max(vals):,.2f}, 最小={min(vals):,.2f}")

    return "\n".join(lines)
