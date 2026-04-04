#!/usr/bin/env python3
"""
ВИМЕР — Визуальные Маркеры Естественной Речи
GUI Entry Point
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
