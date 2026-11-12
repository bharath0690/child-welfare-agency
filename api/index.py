"""Vercel entry point. Vercel's Python runtime serves the WSGI callable named `app`."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cwa.api import app  # noqa: E402,F401
