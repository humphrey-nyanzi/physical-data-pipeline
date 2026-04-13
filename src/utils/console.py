"""
console.py – Pretty terminal output for the FUFA Match Analysis CLI.

Uses raw ANSI escape codes (no external dependencies) so it works on
any modern terminal (Windows 10+, macOS, Linux, VS Code integrated
terminal).

Usage
-----
    from src.utils.console import Console, PipelineFormatter
    Console.banner("FUFA Match Analysis")
    Console.section("Phase 1: Data Cleaning")
    Console.success("Pipeline complete  –  1 204 rows written")
    Console.warning("3 rows dropped (invalid split_name)")
    Console.error("Input file not found")
    Console.stat("Rows retained", 1204, 1300)

    # Drop-in logging Formatter:
    handler = logging.StreamHandler()
    handler.setFormatter(PipelineFormatter())
"""

import logging
import sys
import os

# ──────────────────────────────────────────────────────────────────────────────
# Encoding & Compatibility
# ──────────────────────────────────────────────────────────────────────────────

# Enable ANSI on Windows (requires Windows 10 version 1511+)
if sys.platform == "win32":
    os.system("")  # Activates VT processing on legacy cmd.exe

def _is_utf8():
    """Check if stdout supports UTF-8 characters."""
    encoding = sys.stdout.encoding or "ascii"
    return "utf-8" in encoding.lower()

_BOX = {
    "TL": "╔" if _is_utf8() else "+",
    "TR": "╗" if _is_utf8() else "+",
    "BL": "╚" if _is_utf8() else "+",
    "BR": "╝" if _is_utf8() else "+",
    "H":  "═" if _is_utf8() else "=",
    "V":  "║" if _is_utf8() else "|",
    "h":  "─" if _is_utf8() else "-",
    "v":  "│" if _is_utf8() else "|",
    "sTL": "┌" if _is_utf8() else "+",
    "sTR": "┐" if _is_utf8() else "+",
    "sBL": "└" if _is_utf8() else "+",
    "sBR": "┘" if _is_utf8() else "+",
    "divider": "·" if _is_utf8() else ".",
    "info": "ℹ" if _is_utf8() else "i",
    "success": "✔" if _is_utf8() else "v",
    "warning": "⚠" if _is_utf8() else "!",
    "error": "✖" if _is_utf8() else "x",
    "save": "💾" if _is_utf8() else "S",
    "arrow": "↳" if _is_utf8() else "->",
    "bullet": "·" if _is_utf8() else "-",
    "ellipsis": "…" if _is_utf8() else "...",
}

class _A:  # Namespace for ANSI codes
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"

    # Foreground colours
    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    # Bright foreground
    BRED    = "\033[91m"
    BGREEN  = "\033[92m"
    BYELLOW = "\033[93m"
    BBLUE   = "\033[94m"
    BMAGENTA= "\033[95m"
    BCYAN   = "\033[96m"
    BWHITE  = "\033[97m"

    # Background
    BG_BLACK  = "\033[40m"
    BG_BLUE   = "\033[44m"
    BG_CYAN   = "\033[46m"

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

_WIDTH = 72  # Total banner/divider width

def _paint(*parts) -> str:
    """Join ANSI fragments and reset at the end."""
    return "".join(parts) + _A.RESET


def _print(text: str, *, file=sys.stdout):
    print(text, file=file)


# ──────────────────────────────────────────────────────────────────────────────
# Public Console API
# ──────────────────────────────────────────────────────────────────────────────

class Console:
    """Static helpers for structured, colourful terminal output."""

    @staticmethod
    def _is_utf8() -> bool:
        """Check if stdout supports UTF-8 characters."""
        encoding = sys.stdout.encoding or "ascii"
        return "utf-8" in encoding.lower()

    # ── Structural ────────────────────────────────────────────────────────────

    @staticmethod
    def banner(title: str, subtitle: str = ""):
        """Print a prominent startup banner."""
        pad = _BOX["H"] * _WIDTH
        inner = title.center(_WIDTH)
        lines = [
            "",
            _paint(_A.BOLD, _A.BBLUE, _BOX["TL"], pad, _BOX["TR"]),
            _paint(_A.BOLD, _A.BBLUE, _BOX["V"], _A.BWHITE, _A.BOLD, inner, _A.RESET, _A.BOLD, _A.BBLUE, _BOX["V"]),
        ]
        if subtitle:
            sub_inner = subtitle.center(_WIDTH)
            lines.append(_paint(_A.BBLUE, _BOX["V"], _A.DIM, _A.CYAN, sub_inner, _A.RESET, _A.BBLUE, _BOX["V"]))
        lines += [
            _paint(_A.BOLD, _A.BBLUE, _BOX["BL"], pad, _BOX["BR"]),
            "",
        ]
        _print("\n".join(lines))

    @staticmethod
    def section(title: str):
        """Print a section header (phase separator)."""
        bar = _BOX["h"] * (_WIDTH - len(title) - 3)
        _print(
            "\n"
            + _paint(_A.BOLD, _A.BCYAN, _BOX["sTL"] + _BOX["h"] + f" {title} ", _A.DIM, _A.CYAN, bar)
        )

    @staticmethod
    def section_end():
        """Print a subtle section close line."""
        _print(_paint(_A.DIM, _A.CYAN, _BOX["sBL"] + _BOX["h"] * _WIDTH))

    @staticmethod
    def divider():
        """Faint horizontal rule between logical blocks."""
        _print(_paint(_A.DIM, "  " + _BOX["divider"] * (_WIDTH - 2)))

    # ── Log-level messages ────────────────────────────────────────────────────

    @staticmethod
    def info(message: str):
        prefix = _paint(_A.BBLUE, f"  {_BOX['info']}")
        _print(f"{prefix}  {message}")

    @staticmethod
    def success(message: str):
        prefix = _paint(_A.BGREEN, _A.BOLD, f"  {_BOX['success']}")
        _print(f"{prefix}  {_paint(_A.BGREEN, message)}")

    @staticmethod
    def warning(message: str):
        prefix = _paint(_A.BYELLOW, _A.BOLD, f"  {_BOX['warning']}")
        _print(f"{prefix}  {_paint(_A.BYELLOW, message)}", file=sys.stderr)

    @staticmethod
    def error(message: str):
        prefix = _paint(_A.BRED, _A.BOLD, f"  {_BOX['error']}")
        _print(f"{prefix}  {_paint(_A.BRED, _A.BOLD, message)}", file=sys.stderr)

    @staticmethod
    def debug(message: str):
        prefix = _paint(_A.DIM, f"  {_BOX['bullet']}")
        _print(_paint(_A.DIM, f"{prefix} {message}"))

    # ── Data / statistics ─────────────────────────────────────────────────────

    @staticmethod
    def stat(label: str, value, total=None, *, unit: str = ""):
        """Print a key/value statistic (optionally with a total for context)."""
        val_str = f"{value:,}" if isinstance(value, int) else str(value)
        if unit:
            val_str += f" {unit}"
        if total is not None:
            pct = (value / total * 100) if total else 0
            total_str = f"{total:,}" if isinstance(total, int) else str(total)
            extra = _paint(_A.DIM, f"  / {total_str}  [{pct:.1f}%]")
        else:
            extra = ""
        label_part = _paint(_A.DIM, _A.WHITE, f"  {label:<35}")
        value_part = _paint(_A.BOLD, _A.BWHITE, val_str)
        _print(f"{label_part}{value_part}{extra}")

    @staticmethod
    def rejection_summary(step: str, dropped: int, total: int, reason: str = ""):
        """Print a data-loss summary line (used after each filter step)."""
        if dropped == 0:
            return
        pct = (dropped / total * 100) if total else 0
        arrow  = _paint(_A.BYELLOW, f"  {_BOX['arrow']}")
        label  = _paint(_A.BYELLOW, f" [{step}]")
        count  = _paint(_A.BOLD, _A.BYELLOW, f" {dropped:,} rows removed")
        detail = _paint(_A.DIM, f"  ({pct:.1f}% of {total:,})")
        reason_str = _paint(_A.DIM, _A.CYAN, f"  {_BOX['arrow']} {reason}") if reason else ""
        _print(f"{arrow}{label}{count}{detail}{reason_str}", file=sys.stderr)

    @staticmethod
    def saved(label: str, path: str):
        """Print a 'file saved' confirmation line."""
        icon  = _paint(_A.BGREEN, f"  {_BOX['save']}")
        lbl   = _paint(_A.DIM, _A.WHITE, f" {label}:")
        p     = _paint(_A.BCYAN, f" {path}")
        _print(f"{icon}{lbl}{p}")

    @staticmethod
    def tag(text: str, color: str = "cyan"):
        """Inline coloured tag, returned as string (not printed)."""
        c = {"cyan": _A.BCYAN, "green": _A.BGREEN,
             "yellow": _A.BYELLOW, "red": _A.BRED,
             "blue": _A.BBLUE, "magenta": _A.BMAGENTA}.get(color, _A.BCYAN)
        return _paint(c, _A.BOLD, f"[{text}]")

    @staticmethod
    def pipeline_complete(name: str, rows_out: int):
        """Big 'pipeline complete' celebration line."""
        pad = _BOX["H"] * _WIDTH
        msg = f"  {name.upper()} PIPELINE COMPLETE  {_BOX['bullet']}  {rows_out:,} rows output  "
        _print("")
        _print(_paint(_A.BOLD, _A.BGREEN, _BOX["TL"], pad, _BOX["TR"]))
        _print(_paint(_A.BOLD, _A.BGREEN, _BOX["V"], _A.BWHITE, _A.BOLD, msg.center(_WIDTH), _A.RESET, _A.BOLD, _A.BGREEN, _BOX["V"]))
        _print(_paint(_A.BOLD, _A.BGREEN, _BOX["BL"], pad, _BOX["BR"]))
        _print("")

    @staticmethod
    def pipeline_failed(name: str, reason: str = ""):
        """Pipeline failure box."""
        pad = _BOX["H"] * _WIDTH
        msg = f"  {name.upper()} PIPELINE FAILED  "
        _print("")
        _print(_paint(_A.BOLD, _A.BRED, _BOX["TL"], pad, _BOX["TR"]), file=sys.stderr)
        _print(_paint(_A.BOLD, _A.BRED, _BOX["V"], _A.BWHITE, _A.BOLD, msg.center(_WIDTH), _A.RESET, _A.BOLD, _A.BRED, _BOX["V"]), file=sys.stderr)
        if reason:
            r = f"  Reason: {reason}  "
            _print(_paint(_A.BRED, _BOX["V"], _A.DIM, _A.WHITE, r.center(_WIDTH), _A.RESET, _A.BRED, _BOX["V"]), file=sys.stderr)
        _print(_paint(_A.BOLD, _A.BRED, _BOX["BL"], pad, _BOX["BR"]), file=sys.stderr)
        _print("")

# ──────────────────────────────────────────────────────────────────────────────
# Logging Formatter  (drop-in replacement for basicConfig)
# ──────────────────────────────────────────────────────────────────────────────

_LEVEL_STYLES = {
    logging.DEBUG:    (_A.DIM,    f"{_BOX['bullet']}  DEBUG  {_BOX['bullet']}"),
    logging.INFO:     (_A.BBLUE,  "  INFO   "),
    logging.WARNING:  (_A.BYELLOW,f"{_BOX['warning']}  WARN   "),
    logging.ERROR:    (_A.BRED,   f"{_BOX['error']}  ERROR  "),
    logging.CRITICAL: (_A.BRED + _A.BOLD, "!!  CRIT   "),
}


class PipelineFormatter(logging.Formatter):
    """
    Coloured, structured log formatter for the pipeline CLI.

    Output format:
        HH:MM:SS  [LEVEL]  [PIPELINE]  message text
    """

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        colour, label = _LEVEL_STYLES.get(record.levelno, (_A.WHITE, "  LOG    "))

        # Timestamp
        ts = self.formatTime(record, "%H:%M:%S")
        ts_str = _paint(_A.DIM, ts)

        # Level badge
        lvl_str = _paint(colour, _A.BOLD, f" {label} ")

        # Logger name -> extract pipeline tag if present
        name = record.name.split(".")[-1]  # last component of dotted name
        if len(name) <= 12:
            name_str = _paint(_A.DIM, _A.CYAN, f" [{name:<12}]")
        else:
            name_str = _paint(_A.DIM, _A.CYAN, f" [{name[:12]}{_BOX['ellipsis']}]")

        # Message
        msg = record.getMessage()
        if record.levelno >= logging.ERROR:
            msg_str = _paint(_A.BRED, msg)
        elif record.levelno == logging.WARNING:
            msg_str = _paint(_A.BYELLOW, msg)
        elif record.levelno == logging.DEBUG:
            msg_str = _paint(_A.DIM, msg)
        else:
            msg_str = msg

        line = f"{ts_str}{lvl_str}{name_str}  {msg_str}"

        # Attach exception info if present
        if record.exc_info:
            exc = self.formatException(record.exc_info)
            line += "\n" + _paint(_A.DIM, _A.RED, exc)

        return line


def setup_console_logging(verbose: bool = False) -> None:
    """
    Configure root logger to use PipelineFormatter on stderr.

    Call this ONCE at the start of main().
    """
    level = logging.DEBUG if verbose else logging.INFO
    root = logging.getLogger()
    root.setLevel(level)

    # Remove any default handlers added by basicConfig
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(PipelineFormatter())
    root.addHandler(handler)
