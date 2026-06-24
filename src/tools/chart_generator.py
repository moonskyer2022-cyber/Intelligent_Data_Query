import os
import uuid
from typing import Any, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

from settings import CHART_OUTPUT_DIR

_CHINESE_FONT = None
_CHART_KEYWORDS = (
    "图表",
    "图形",
    "可视化",
    "画图",
    "绘制",
    "柱状图",
    "条形图",
    "折线图",
    "饼图",
    "圆饼图",
    "趋势图",
    "对比图",
    "分布图",
    "统计图",
    "chart",
    "graph",
    "plot",
    "visualization",
)


def _setup_chinese_font():
    global _CHINESE_FONT
    if _CHINESE_FONT:
        return _CHINESE_FONT

    for font_path in (
        "C:\\Windows\\Fonts\\msyh.ttc",
        "C:\\Windows\\Fonts\\simhei.ttf",
        "C:\\Windows\\Fonts\\simsun.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ):
        if not os.path.exists(font_path):
            continue
        try:
            prop = fm.FontProperties(fname=font_path)
            plt.rcParams["font.family"] = prop.get_name()
            plt.rcParams["axes.unicode_minus"] = False
            _CHINESE_FONT = prop
            return prop
        except Exception:
            continue
    return None


def _get_font(size: int = 10):
    font = _setup_chinese_font()
    return fm.FontProperties(fname=font.get_file(), size=size) if font else None


def _extract_data(data: list[dict[str, Any]], x_field: str, y_field: str):
    labels, values = [], []
    for item in data:
        fields = item.get("fields", item) if isinstance(item, dict) else {}
        try:
            y_val = float(fields.get(y_field, 0) or 0)
        except (ValueError, TypeError):
            y_val = 0
        labels.append(str(fields.get(x_field, "")))
        values.append(y_val)
    return labels, values


def should_generate_chart(user_question: str) -> bool:
    q = user_question.lower()
    return any(keyword in q for keyword in _CHART_KEYWORDS)


def infer_chart_config(user_question: str, data: list[dict[str, Any]]) -> dict[str, str]:
    config = {
        "chart_type": "bar",
        "x_field": "",
        "y_field": "",
        "title": "数据图表",
        "x_label": "",
        "y_label": "",
    }

    user_lower = user_question.lower()
    if any(keyword in user_lower for keyword in ("饼图", "圆饼图", "pie", "占比", "比例", "分布")):
        config["chart_type"] = "pie"
    elif any(keyword in user_lower for keyword in ("折线图", "line", "趋势", "变化", "走势")):
        config["chart_type"] = "line"
    elif any(keyword in user_lower for keyword in ("条形图", "水平", "horizontal")):
        config["chart_type"] = "horizontal_bar"

    if data:
        sample = data[0].get("fields", data[0]) if isinstance(data[0], dict) else {}
        fields = list(sample.keys())

        name_fields = [
            field
            for field in fields
            if field in ("product_name", "category_name", "user_name", "brand", "region", "province", "member_level", "order_no")
            or "name" in field
            or field in ("region", "channel")
        ]
        config["x_field"] = name_fields[0] if name_fields else (fields[0] if fields else "")

        value_fields = [
            field
            for field in fields
            if field in ("total_amount", "line_amount", "discount_amount", "price", "quantity", "stock", "cost")
        ]
        if not value_fields:
            value_fields = [field for field in fields if any(key in field for key in ("amount", "price", "quantity", "stock"))]
        if value_fields:
            config["y_field"] = value_fields[0]
        else:
            for field in fields:
                if isinstance(sample.get(field), (int, float)):
                    config["y_field"] = field
                    break

    if "销售" in user_question or "金额" in user_question or "gmv" in user_lower:
        config["title"] = "销售数据统计"
        config["y_field"] = config.get("y_field") or "total_amount"
    elif "价格" in user_question:
        config["title"] = "商品价格对比"
        config["y_field"] = "price"

    config["x_label"] = config["x_field"]
    config["y_label"] = config["y_field"] or ""
    return config


def generate_chart(
    data: list[dict[str, Any]],
    chart_type: str,
    x_field: str,
    y_field: str,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    color: Optional[str] = None,
    figsize: tuple = (12, 7),
) -> str:
    _setup_chinese_font()
    labels, values = _extract_data(data, x_field, y_field)
    if not labels:
        raise ValueError("没有有效数据用于生成图表")

    fig, ax = plt.subplots(figsize=figsize)
    font_title = _get_font(16)
    font_label = _get_font(12)
    max_val = max(values) if values else 0
    bar_color = color or "#4472C4"

    if chart_type == "bar":
        bars = ax.bar(range(len(labels)), values, color=bar_color, width=0.6)
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max_val * 0.02,
                f"{val:,.0f}",
                ha="center",
                va="bottom",
                fontsize=10,
            )
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=35, ha="right")
        ax.set_ylim(0, max_val * 1.15 if max_val else 1)
        ax.grid(axis="y", alpha=0.3, linestyle="--")
    elif chart_type == "line":
        ax.plot(range(len(labels)), values, marker="o", linewidth=2, color=bar_color)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=35, ha="right")
        ax.grid(True, alpha=0.3, linestyle="--")
    elif chart_type == "pie":
        non_zero = [(label, val) for label, val in zip(labels, values) if val > 0]
        if not non_zero:
            raise ValueError("没有有效的非零数据")
        pie_labels, pie_values = zip(*non_zero)
        ax.pie(pie_values, labels=pie_labels, autopct="%1.1f%%", startangle=90)
    elif chart_type == "horizontal_bar":
        ax.barh(range(len(labels)), values, color=bar_color)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=0.3, linestyle="--")
    else:
        ax.bar(range(len(labels)), values, color=bar_color)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=35, ha="right")

    if title:
        ax.set_title(title, fontproperties=font_title, fontweight="bold", pad=12)
    if x_label and chart_type not in ("pie", "horizontal_bar"):
        ax.set_xlabel(x_label, fontproperties=font_label)
    if y_label and chart_type != "pie":
        ax.set_ylabel(y_label, fontproperties=font_label)

    plt.tight_layout()
    CHART_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"chart_{uuid.uuid4().hex[:8]}.png"
    filepath = CHART_OUTPUT_DIR / filename
    fig.savefig(filepath, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    return f"/static/charts/{filename}"
