from __future__ import annotations

from pathlib import Path

__all__ = ["__version__"]

__version__ = "0.1.0"

_SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "feicai_seedance"
__path__ = [str(_SRC_PACKAGE)]
