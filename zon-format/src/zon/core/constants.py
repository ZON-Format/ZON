"""ZON Protocol Constants.

This module defines all constants used throughout the ZON encoding and decoding
process, including format markers, security limits, and legacy compatibility settings.
"""

VERSION = "1.0.3"

TABLE_MARKER = "@"
META_SEPARATOR = ":"

GAS_TOKEN = "_"
LIQUID_TOKEN = "^"

DEFAULT_ANCHOR_INTERVAL = 100

MAX_DOCUMENT_SIZE = 100 * 1024 * 1024
MAX_LINE_LENGTH = 1024 * 1024
MAX_ARRAY_LENGTH = 1_000_000
MAX_OBJECT_KEYS = 100_000
MAX_NESTING_DEPTH = 100

LEGACY_TABLE_MARKER = "@"
INLINE_THRESHOLD_ROWS = 0
SINGLETON_THRESHOLD = 1

DICT_REF_PREFIX = "%"
ANCHOR_PREFIX = "$"
REPEAT_SUFFIX = "x"
