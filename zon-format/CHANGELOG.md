# Changelog

## [1.2.0] - 2024-12-07

### Added
- **Delta Encoding**: Efficient encoding for numeric sequences (e.g., `id:delta`).
- **Dictionary Compression**: Compression for repetitive string columns.
- **LLM Optimization**: `encode_llm` for token-efficient prompts.
- **Advanced Schema Validation**:
    - Regex patterns (`.regex()`)
    - UUID validation (`.uuid()`)
    - DateTime validation (`.datetime()`, `.date()`, `.time()`)
    - Literal values (`.literal()`)
    - Union types (`.union()`)
    - Default values (`.default()`)
    - Custom refinements (`.refine()`)
- **CLI**: Full implementation of `convert`, `validate`, `stats`, and `format` commands.

### Changed
- **Decoder**: `decode` method now accepts `type_coercion` and `strict` keyword arguments.
- **Performance**: Improved table parsing and sparse field handling.

### Fixed
- **CLI**: Fixed relative import issues and command execution.
- **Schema**: Fixed missing validation methods (`min`, `max`, `email`, etc.).


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Fixed
- **Package Exports**: Fixed `AttributeError` by properly exporting `encode` and `decode` functions in `zon/__init__.py`.

## [1.0.4] - 2025-11-30

### Added
- **Colon-less Syntax:** Objects and arrays in nested positions now use `key{...}` and `key[...]` syntax, removing redundant colons.
- **Smart Flattening:** Top-level nested objects are automatically flattened to dot notation (e.g., `config.db{...}`).
- **Control Character Escaping:** All control characters (ASCII 0-31) are now properly escaped to prevent binary file creation.
- **Runtime Schema Validation:** New `zon` builder and `validate()` function for LLM guardrails.
- **Algorithmic Benchmark Generation**: Replaced LLM-based question generation with deterministic algorithm for consistent benchmarks.
- **Expanded Dataset**: Added "products" and "feed" data to unified dataset for real-world e-commerce scenarios.
- **Tricky Questions**: Introduced edge cases (non-existent fields, logic traps, case sensitivity) to stress-test LLM reasoning.
- **Robust Benchmark Runner**: Added exponential backoff and rate limiting to handle Azure OpenAI S0 tier constraints.

### Changed
- **Benchmark Formats**: Refined tested formats to ZON, TOON, JSON, JSON (Minified), and CSV for focused analysis.
- **Documentation**: Updated README and API references with the latest benchmark results (GPT-5 Nano) and accurate token counts.
- **Token Efficiency**: Recalculated efficiency scores based on the expanded dataset, confirming ZON's leadership (1430.6 score).

### Improved
- **Token Efficiency:** Achieved up to 23.8% reduction vs JSON (GPT-4o) thanks to syntax optimizations.
- **Readability:** Cleaner, block-like structure for nested data.

### Fixed
- **Critical Data Integrity**: Fixed roundtrip failures for strings containing newlines, empty strings, and escaped characters.
- **Decoder Logic**: Fixed `_split_by_delimiter` to correctly handle nested arrays and objects within table cells (e.g., `[10, 20]`).
- **Encoder Logic**: Added mandatory quoting for empty strings and strings with newlines to prevent data loss.
- **Rate Limiting**: Resolved 429 errors during benchmarking with robust retry logic.

## [1.0.3] - 2025-11-28

### 🎯 100% LLM Retrieval Accuracy Achieved

**Major Achievement**: ZON now achieves **100% LLM retrieval accuracy** while maintaining superior token efficiency over TOON!

### Changed
- **Explicit Sequential Columns**: Disabled automatic sequential column omission (`[id]` notation)
  - All columns now explicitly listed in table headers for better LLM comprehension
  - Example: `users:@(5):active,id,lastLogin,name,role` (was `users:@(5)[id]:active,lastLogin,name,role`)
  - Trade-off: +1.7% token increase for 100% LLM accuracy

### Performance
- **LLM Accuracy**: 100% (24/24 questions) vs TOON 100%, JSON 91.7%
- **Token Efficiency**: 19,995 tokens (5.0% fewer than TOON's 20,988)
- **Overall Savings vs TOON**: 4.6% (Claude) to 17.6% (GPT-4o)

### Quality
- ✅ All unit tests pass (28/28)
- ✅ All roundtrip tests pass (27/27 datasets)
- ✅ No data loss or corruption
- ✅ Production ready

## [1.0.2] - 2025-11-24

### Changed - "ClearText" Major Format Overhaul

#### Format Improvements
- **Removed protocol overhead**: Eliminated `#Z:`, `|` pipes, and complex header markers
- **YAML-like metadata**: Changed from `M=key="val"` to clean `key:val` syntax
- **Clean @table syntax**: Replaced schema markers with readable `@tablename(count):cols`
- **Aggressive quote removal**: Only quote when absolutely necessary (commas, control chars)
- **Compact array syntax**: `[item1,item2,item3]` with minimal inner quotes
- **No spaces after separators**: Removed spaces after `:` and `,` for compactness

#### Performance
- **31.9% compression** vs JSON (up from 27.4%)
- **25.6% better** than TOON (up from 20.8%)
- Tested on 318 records across 6 real-world datasets

## [1.0.0] - 2025-11-23

### Added - Initial Release
- ZON v1.0 format implementation
- Full encoder/decoder with lossless round-trips
- CLI tool for encoding/decoding
- Comprehensive test suite

[1.0.5]: https://github.com/ZON-Format/ZON/releases/tag/v1.0.5
[1.0.4]: https://github.com/ZON-Format/ZON/releases/tag/v1.0.4
[1.0.3]: https://github.com/ZON-Format/ZON/releases/tag/v1.0.3
[1.0.2]: https://github.com/ZON-Format/ZON/releases/tag/v1.0.2
[1.0.0]: https://github.com/ZON-Format/ZON/releases/tag/v1.0.0
