# ZON Specification v1.0

## Overview

ZON is a binary-safe, human-readable serialization format designed to minimize token usage for LLMs.

## States

### GAS (Generative)
Used for highly predictable data sequences.
- **Syntax:** `DEF <column> = RANGE(<start>, STEP=<step>)`
- **Behavior:** The decoder generates values based on the rule.

### LIQUID (Differential)
Used for low-cardinality, repetitive data.
- **Syntax:** `DEF <column> = LIQUID`
- **Token:** `^` (Ditto)
- **Behavior:** If the value is `^`, repeat the value from the previous row.

### SOLID (Explicit)
Used for high-entropy data.
- **Syntax:** Default state.
- **Behavior:** Values are explicitly written (JSON-like strings, numbers).

## Safety Anchors

To prevent "Hallucination Drift", ZON enforces a Calibration Anchor every N rows.
- **Syntax:** `#ANCHOR_EVERY=<N>`
- **Behavior:** Every Nth row is fully explicit (SOLID), regardless of the column state. This allows the decoder (and LLM) to re-ground its state.

## Format Structure

```
#ZON v1.0
<Header Definitions>
#ANCHOR_EVERY=<N>
--------------------
<Data Rows>
```
