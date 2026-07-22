import re

_slug_re = re.compile(r"\w+")

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
    slug = "_".join(_slug_re.findall(message)).lower()
    if len(slug) > truncate_slug_length:
        slug = slug[:truncate_slug_length].rsplit("_", 1)[0] + "_"
    return slug    