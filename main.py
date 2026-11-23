"""Titik masuk aplikasi SI-Kos.

Jalankan: python main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db  # noqa: E402
from ui.app import Aplikasi  # noqa: E402


def main() -> int:
    try:
        conn = db.siapkan_database()
    except Exception as e:
        print(f"Database tidak dapat disiapkan: {e}", file=sys.stderr)
        return 1
    app = Aplikasi(conn)
    app.mainloop()
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
