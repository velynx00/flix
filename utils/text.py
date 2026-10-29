# ============================================================
# utils/text.py — Small-Caps Unicode Converter + Text Helpers
# Converts regular ASCII into Unicode small-cap equivalents
# so every message rendered by the bot has a consistent style.
# ============================================================

from __future__ import annotations

# ── Small-caps mapping table ──────────────────────────────────
# Each ASCII letter maps to its Unicode small-capital counterpart.
# Digits and punctuation are passed through unchanged.
_SMALL_CAPS_MAP: dict[str, str] = {
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ",
    "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ",
    "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ",
    "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ",
    "q": "ǫ", "r": "ʀ", "s": "ꜱ", "t": "ᴛ",
    "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x",
    "y": "ʏ", "z": "ᴢ",
    # uppercase maps to the same small-cap glyph
    "A": "ᴀ", "B": "ʙ", "C": "ᴄ", "D": "ᴅ",
    "E": "ᴇ", "F": "ꜰ", "G": "ɢ", "H": "ʜ",
    "I": "ɪ", "J": "ᴊ", "K": "ᴋ", "L": "ʟ",
    "M": "ᴍ", "N": "ɴ", "O": "ᴏ", "P": "ᴘ",
    "Q": "ǫ", "R": "ʀ", "S": "ꜱ", "T": "ᴛ",
    "U": "ᴜ", "V": "ᴠ", "W": "ᴡ", "X": "x",
    "Y": "ʏ", "Z": "ᴢ",
}


def sc(text: str) -> str:
    """
    Convert a plain-ASCII string into Unicode small-caps.

    Parameters
    ----------
    text : str
        The input string to convert.

    Returns
    -------
    str
        The converted string with small-cap Unicode glyphs.

    Example
    -------
    >>> sc("Hello World")
    'ʜᴇʟʟᴏ ᴡᴏʀʟᴅ'
    """
    return "".join(_SMALL_CAPS_MAP.get(ch, ch) for ch in text)


def sc_upper(text: str) -> str:
    """
    Same as sc() but first uppercases the input.
    Useful for section headings where all-caps is desired before conversion.

    Parameters
    ----------
    text : str
        The input string to convert.

    Returns
    -------
    str
        Uppercase-then-small-capped string.
    """
    return sc(text.upper())


def truncate(text: str, max_len: int = 50, suffix: str = "…") -> str:
    """
    Truncate a string to *max_len* characters and append *suffix* if cut.

    Parameters
    ----------
    text    : str   — Input string.
    max_len : int   — Maximum visible length before truncating (default 50).
    suffix  : str   — What to append when truncated (default ellipsis char).

    Returns
    -------
    str
        The (possibly truncated) string.
    """
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def escape_html(text: str) -> str:
    """
    Escape characters that conflict with Telegram's HTML parse mode.

    Parameters
    ----------
    text : str
        Raw text that may contain <, >, & characters.

    Returns
    -------
    str
        HTML-safe string.
    """
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_progress_bar(current: int, total: int, width: int = 10) -> str:
    """
    Build a simple Unicode block-character progress bar.

    Parameters
    ----------
    current : int   — How many units are complete.
    total   : int   — Total number of units.
    width   : int   — Number of block characters in the bar (default 10).

    Returns
    -------
    str
        A string like '████░░░░░░ 4/10'.
    """
    if total <= 0:
        return f"░{'░' * width} 0/0"
    filled = int((current / total) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {current}/{total}"


def format_number(n: int) -> str:
    """
    Format a large integer with comma separators.

    Parameters
    ----------
    n : int — The number to format.

    Returns
    -------
    str
        Formatted string e.g. '1,234,567'.
    """
    return f"{n:,}"


def seconds_to_human(seconds: int) -> str:
    """
    Convert a number of seconds into a human-readable duration string.

    Parameters
    ----------
    seconds : int — Duration in seconds.

    Returns
    -------
    str
        E.g. '2h 30m 15s', '45m 0s', '10s'.
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


# ── Pre-built small-cap label constants ───────────────────────
# Re-used across handlers to avoid re-computing the same strings.

LABEL_SCRAPE   = sc("scrape")
LABEL_ADD      = sc("add")
LABEL_PREMIUM  = sc("premium")
LABEL_UPDATES  = sc("updates")
LABEL_ADMIN    = sc("admin panel")
LABEL_CANCEL   = sc("cancel")
LABEL_BACK     = sc("back")
LABEL_DONE     = sc("done")
LABEL_STATUS   = sc("status")
LABEL_SESSIONS = sc("sessions")
LABEL_MYPLAN   = sc("my plan")
LABEL_HELP     = sc("help")
LABEL_YES      = sc("yes, proceed")
LABEL_NO       = sc("no, cancel")
LABEL_REVOKE   = sc("revoke session")
LABEL_EXPORT   = sc("export csv")
LABEL_GRANT    = sc("grant premium")
LABEL_REVOKE_P = sc("revoke premium")
LABEL_STATS    = sc("bot stats")
LABEL_BCAST    = sc("broadcast")
