import re
from typing import Any

from app.logger import logger

# 初始内置模型映射
MODEL_MAP: dict[str, str] = {
    "claude-opus4.6": "avocado-froyo-medium",
    "claude-sonnet4.6": "almond-croissant-low",
    "gemini-3.1pro": "galette-medium-thinking",
    "gpt-5.2": "oatmeal-cookie",
    "gpt-5.4": "oval-kumquat-medium",
}

NOTION_MODEL_REVERSE_MAP: dict[str, str] = {value: key for key, value in MODEL_MAP.items()}

DISPLAY_NAMES: dict[str, str] = {
    "claude-opus4.6": "Claude Opus 4.6",
    "claude-sonnet4.6": "Claude Sonnet 4.6",
    "gemini-3.1pro": "Gemini 3.1 Pro",
    "gpt-5.2": "GPT-5.2",
    "gpt-5.4": "GPT-5.4",
}

MODEL_ICONS: dict[str, str] = {
    "claude-opus4.6": "✳️",
    "claude-sonnet4.6": "✳️",
    "gemini-3.1pro": "✦",
    "gpt-5.2": "⚙",
    "gpt-5.4": "⚙",
}

# 默认使用 Sonnet 4.6
DEFAULT_MODEL = "claude-sonnet4.6"


def update_dynamic_models(models_list: list[dict[str, Any]]):
    """
    根据从 Notion API 获取的原始列表，动更新模型映射。
    """
    if not models_list:
        return

    new_model_map = {}
    new_display_names = {}
    new_model_icons = {}

    for m in models_list:
        notion_id = m.get("model")
        display_name = m.get("modelMessage")
        family = m.get("modelFamily", "").lower()

        if not notion_id or not display_name:
            continue

        # 生成标准 ID (例如 "Claude 3.5 Sonnet" -> "claude-3.5-sonnet")
        standard_id = display_name.lower().replace(" ", "-")
        # 移除非字母数字字符（保留横杠和点）
        standard_id = re.sub(r"[^a-z0-9\-\.]", "", standard_id)

        # 补全前缀
        if family == "anthropic" and not standard_id.startswith("claude"):
            standard_id = f"claude-{standard_id}"
        elif family == "gemini" and not standard_id.startswith("gemini"):
            standard_id = f"gemini-{standard_id}"
        elif family == "openai" and not standard_id.startswith("gpt"):
            standard_id = f"gpt-{standard_id}"

        new_model_map[standard_id] = notion_id
        new_display_names[standard_id] = display_name

        # 分配图标
        if family == "anthropic":
            new_model_icons[standard_id] = "✳️"
        elif family == "openai":
            new_model_icons[standard_id] = "⚙"
        elif family == "gemini":
            new_model_icons[standard_id] = "✦"
        else:
            new_model_icons[standard_id] = "❓"

    # 特殊处理：确保原有的主要 ID 依然可用（如果存在且 Notion 还在支持对应的 notion_id）
    # 例如，如果 notion 还在支持 'almond-croissant-low'，但它的名字变了，
    # 我们仍然让 'claude-sonnet4.6' 指向它。
    reverse_new_map = {v: k for k, v in new_model_map.items()}
    legacy_ids = {
        "claude-opus4.6": "avocado-froyo-medium",
        "claude-sonnet4.6": "almond-croissant-low",
        "gemini-3.1pro": "galette-medium-thinking",
        "gpt-5.2": "oatmeal-cookie",
        "gpt-5.4": "oval-kumquat-medium",
    }
    for lid, nid in legacy_ids.items():
        # 如果新生成的 ID 已经包含了这个 legacy ID（或者新生成的 ID 本身就是这个格式），则跳过，避免重复
        if nid in reverse_new_map:
            new_id = reverse_new_map[nid]
            if new_id == lid:
                continue

            new_model_map[lid] = nid
            # display_name 和 icon 保持原样或从 new 中继承
            new_display_names[lid] = new_display_names.get(new_id, lid.replace("-", " ").title())
            new_model_icons[lid] = new_model_icons.get(new_id, "❓")


    # 原子更新全局辞书
    MODEL_MAP.clear()
    MODEL_MAP.update(new_model_map)

    DISPLAY_NAMES.clear()
    DISPLAY_NAMES.update(new_display_names)

    MODEL_ICONS.clear()
    MODEL_ICONS.update(new_model_icons)

    NOTION_MODEL_REVERSE_MAP.clear()
    NOTION_MODEL_REVERSE_MAP.update({v: k for k, v in MODEL_MAP.items()})

    logger.info(f"Dynamically updated {len(MODEL_MAP)} models from Notion AI")


def get_notion_model(model_name: str) -> str:
    # If the input is already a known Notion internal model ID (a value in MODEL_MAP),
    # return it as-is to prevent double-conversion fallback to the default model.
    if model_name in NOTION_MODEL_REVERSE_MAP:
        return model_name
    return MODEL_MAP.get(model_name, MODEL_MAP.get(DEFAULT_MODEL, "almond-croissant-low"))


def is_gemini_model(model_name: str) -> bool:
    standard_name = get_standard_model(model_name)
    if standard_name.startswith("gemini-"):
        return True
    notion_model = get_notion_model(standard_name)
    return notion_model.startswith("vertex-") or notion_model.startswith("galette-")


def get_thread_type(model_name: str) -> str:
    if is_gemini_model(model_name):
        return "markdown-chat"
    return "workflow"


def get_standard_model(model_name: str) -> str:
    if model_name in MODEL_MAP:
        return model_name
    return NOTION_MODEL_REVERSE_MAP.get(model_name, DEFAULT_MODEL)


def list_available_models() -> list[str]:
    # 返回标准 ID 列表
    return list(MODEL_MAP.keys())


def is_supported_model(model_name: str) -> bool:
    return model_name in MODEL_MAP


def get_display_name(model_name: str) -> str:
    standard_name = get_standard_model(model_name)
    return DISPLAY_NAMES.get(standard_name, standard_name)


def get_model_icon(model_name: str) -> str:
    standard_name = get_standard_model(model_name)
    return MODEL_ICONS.get(standard_name, "")
