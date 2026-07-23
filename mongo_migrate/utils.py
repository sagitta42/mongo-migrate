import re

TARGET_KEYWORDS = ["head", "base", "-1", "+1"]

def slugify_message(message: str, truncate_slug_length: int = 40) -> str:
    """
    Slugify message to create a short cleaned up filename safe identifier.

    Filename incompatible characters (e.g. punctuation, /) are removed.
    Spaces are replaced by underscores.
    All characters converted to lowercase.
    
    >>> slugify_message("add ABCD data/info")
    "add_abcd_data_info"

    Procedure taken from alembic:
    https://github.com/sqlalchemy/alembic/blob/main/alembic/script/base.py    
    """
    _slug_re = re.compile(r"\w+")

    slug = "_".join(_slug_re.findall(message)).lower()
    if len(slug) > truncate_slug_length:
        slug = slug[:truncate_slug_length].rsplit("_", 1)[0] + "_"
    return slug

def timestamp_from_filename(filename: str) -> str:
    """
    Extract timestamp from migration filename.
    """
    return filename.split('_')[0]

def direction_target_is_valid(direction: str, target: str) -> bool:
    """
    Check validity of direction (upgrade/downgrade) and target (timestamp/head/base/+1/-1/...).

    Timestamp is a valid target for all cases.
    head or +1 is only valid for upgrade
    base or -1 is only valid for downgrade
    """
    if not target in TARGET_KEYWORDS:
        return True
    
    upgrade_only_target = target in ["head", "+1"]
    if upgrade_only_target and not direction == "upgrade":
        return False

    downgrade_only_target = target in ["base", "-1"]
    if downgrade_only_target and not direction == "downgrade":
        return False

    return True