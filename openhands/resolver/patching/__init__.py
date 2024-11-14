# -*- coding: utf-8 -*-

from .patch import parse_patch
from .apply import apply_diff

__all__ = ["parse_patch", "apply_diff"]
