# ZON Protocol Constants v1.0.3
VERSION = "1.0.3"

# Format markers
TABLE_MARKER = "@"          # @hikes(3): col1, col2
META_SEPARATOR = ":"        # key:value (no space for compactness)

# Stream Tokens
GAS_TOKEN = "_"             # Gas/placeholder
LIQUID_TOKEN = "^"          # Liquid/variable

# Thresholds
DEFAULT_ANCHOR_INTERVAL = 100

# Security limits (DOS prevention)
MAX_DOCUMENT_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_LINE_LENGTH = 1024 * 1024          # 1 MB
MAX_ARRAY_LENGTH = 1_000_000           # 1 million items
MAX_OBJECT_KEYS = 100_000              # 100K keys
MAX_NESTING_DEPTH = 100                # Already enforced in decoder

# Legacy compatibility (v1.x)
LEGACY_TABLE_MARKER = "@"     # Flatten lists with 1 item to metadata
INLINE_THRESHOLD_ROWS = 0
SINGLETON_THRESHOLD = 1

# Legacy compatibility (kept for potential fallback)
DICT_REF_PREFIX = "%"
ANCHOR_PREFIX = "$"
REPEAT_SUFFIX = "x"
