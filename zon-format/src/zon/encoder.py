import json
import re
from collections import Counter
from typing import List, Dict, Any, Tuple
from .constants import *

class ZonEncoder:
    def __init__(self, anchor_interval: int = DEFAULT_ANCHOR_INTERVAL):
        self.anchor_interval = anchor_interval
        self._safe_str_re = re.compile(r'^[a-zA-Z0-9_\-\.]+$')

    def encode(self, data: List[Dict[str, Any]]) -> str:
        if not data: return "[]"
        flat_data = [self._flatten(row) for row in data]
        
        if len(flat_data) <= INLINE_THRESHOLD_ROWS:
            return self._encode_inline(flat_data)

        all_keys = set().union(*(d.keys() for d in flat_data))
        keys = sorted(list(all_keys))
        
        z_map, z_map_inv = self._build_global_dict(flat_data)
        col_defs = self._analyze_columns(flat_data, keys)
        
        # Header
        schema_parts = []
        for k in keys:
            meta = col_defs[k]
            st = meta['state']
            rule = SOLID_KEYWORD
            
            if st == "GAS_INT": 
                rule = f"{RANGE_KEYWORD}({meta['vals'][0]},{meta['param']})"
            elif st == "GAS_PAT": 
                rule = f"{PATTERN_KEYWORD}({meta['param'][0]},{meta['param'][1]},{meta['param'][2]})"
            elif st == "GAS_MULT": 
                rule = f"{MULT_KEYWORD}({meta['param']})"
            elif st == "LIQUID": 
                rule = LIQUID_KEYWORD
            elif st == "ENUM":
                # E(val1,val2,...)
                enum_vals = ','.join([self._pack_str(v, False) for v in meta['enum_map']])
                rule = f"{ENUM_KEYWORD}({enum_vals})"
            elif st == "VALUE":
                # V(default_value)
                rule = f"{VALUE_KEYWORD}({self._pack_value(meta['default'])})"
            elif st == "DELTA":
                # Δ(base) - base value for first element
                rule = f"{DELTA_KEYWORD}({meta['param']})"
                
            schema_parts.append(f"{k}:{rule}")

        schema_def = f"rows[{len(flat_data)}]{SCHEMA_START}{','.join(schema_parts)}{SCHEMA_END}"
        dict_str = f"{DICT_MARKER}{','.join([self._pack_str(v, False) for v in z_map])}{SEPARATOR}" if z_map else ""
        header = f"{HEADER_PREFIX}{VERSION}{SEPARATOR}{dict_str}{schema_def}{SEPARATOR}{ANCHOR_MARKER}{self.anchor_interval}"
        output = [header]

        # Stream
        prev_row_vals = {k: None for k in keys}
        pending_rle = 0
        
        for i, row in enumerate(flat_data):
            is_anchor = ((i + 1) % self.anchor_interval == 0) or (i == 0)
            
            # Prediction
            is_predictable = not is_anchor
            if is_predictable:
                for k in keys:
                    val = row.get(k)
                    meta = col_defs[k]
                    st = meta['state']
                    
                    if st == "GAS_INT":
                        if val != (meta['vals'][0] + (i * meta['param'])): is_predictable = False
                    elif st == "GAS_PAT":
                        tpl, start, step = meta['param']
                        try:
                            if val != tpl.format(start + (i * step)): is_predictable = False
                        except: is_predictable = False
                    elif st == "LIQUID":
                        if val != prev_row_vals[k]: is_predictable = False
                    elif st == "VALUE":
                        if val != meta['default']: is_predictable = False
                    else: 
                        is_predictable = False
                        
                    if not is_predictable: break

            if is_predictable:
                pending_rle += 1
            else:
                if pending_rle > 0:
                    output.append(f"{pending_rle}{REPEAT_SUFFIX}")
                    pending_rle = 0
                
                line = []
                for k in keys:
                    val = row.get(k)
                    meta = col_defs[k]
                    st = meta['state']
                    
                    # Encode
                    enc = None
                    if st == "GAS_MULT" and val is not None:
                        try: enc = str(int(round(val * meta['param'])))
                        except: enc = self._pack_value(val)
                    elif st == "ENUM" and val in meta['enum_inv']:
                        enc = str(meta['enum_inv'][val])
                    elif st == "DELTA" and i > 0 and val is not None and prev_row_vals[k] is not None:
                        try: enc = str(int(val - prev_row_vals[k]))
                        except: enc = self._pack_value(val)
                    elif isinstance(val, str) and val in z_map_inv:
                        enc = f"{DICT_REF_PREFIX}{z_map_inv[val]}"
                    else:
                        enc = self._pack_value(val)

                    # Write
                    if is_anchor:
                        line.append(enc)
                    else:
                        match = False
                        if st == "GAS_INT" and val == (meta['vals'][0] + (i * meta['param'])): match = True
                        elif st == "LIQUID" and val == prev_row_vals[k]: match = True
                        elif st == "VALUE" and val == meta['default']: match = True
                        line.append("" if match else enc)
                    
                    prev_row_vals[k] = val
                
                prefix = f"{ANCHOR_PREFIX}{i+1}:" if is_anchor else ""
                output.append(f"{prefix}{','.join(line)}")

        if pending_rle > 0: output.append(f"{pending_rle}{REPEAT_SUFFIX}")
        return "\n".join(output)

    def _build_global_dict(self, data):
        c = Counter()
        for r in data:
            for v in r.values():
                if isinstance(v, str): c[v] += 1
        candidates = []
        for val, freq in c.items():
            if len(val) < 3: continue
            if (freq * (len(val)-2)) > (len(val)+5):
                candidates.append((val, freq))
        candidates.sort(key=lambda x: x[1], reverse=True)
        z_map = [x[0] for x in candidates[:64]]
        return z_map, {v: i for i, v in enumerate(z_map)}

    def _analyze_columns(self, data, keys):
        """Entropy Tournament: Test 8 strategies and pick the winner"""
        col_defs = {}
        for k in keys:
            vals = [d.get(k) for d in data]
            state, param = "SOLID", None
            nums = [x for x in vals if isinstance(x, (int, float)) and not isinstance(x, bool)]
            
            # Test all strategies and pick the best
            best_strategy = ("SOLID", None, {})
            best_cost = float('inf')
            
            # Strategy 1: GAS_INT
            if len(nums) == len(vals) and len(vals) > 1:
                try:
                    diffs = {vals[i]-vals[i-1] for i in range(1, len(vals))}
                    if len(diffs) == 1 and abs(list(diffs)[0]) > 1e-9:
                        cost = 0  # Near-zero cost
                        if cost < best_cost:
                            best_strategy = ("GAS_INT", list(diffs)[0], {})
                            best_cost = cost
                except: pass
            
            # Strategy 2: GAS_PAT
            if len(vals) > 1 and isinstance(vals[0], str):
                pat = self._detect_pattern(vals)
                if pat:
                    cost = 0
                    if cost < best_cost:
                        best_strategy = ("GAS_PAT", pat, {})
                        best_cost = cost
            
            # Strategy 3: GAS_MULT
            if len(nums) == len(vals) and len(vals) > 0:
                if all(isinstance(x, float) and (x*100).is_integer() for x in nums):
                    cost = 2  # Small overhead for multiplier
                    if cost < best_cost:
                        best_strategy = ("GAS_MULT", 100.0, {})
                        best_cost = cost
            
            # Strategy 4: ENUM (Local Dictionary)
            try:
                # Only consider hashable values
                hashable_vals = [v for v in vals if v is not None and not isinstance(v, (list, dict))]
                unique_vals = list(set(hashable_vals))
                if len(unique_vals) < 16 and len(unique_vals) > 1:
                    # Cost = header overhead + stream (1-2 digits per value)
                    header_cost = sum(len(str(v)) for v in unique_vals)
                    stream_cost = len(vals) * 1.5  # Avg digits
                    total_cost = header_cost + stream_cost
                    
                    # Compare with explicit
                    explicit_cost = sum(len(str(v)) for v in vals)
                    if total_cost < explicit_cost:
                        enum_map = unique_vals
                        enum_inv = {v: i for i, v in enumerate(enum_map)}
                        if total_cost < best_cost:
                            best_strategy = ("ENUM", None, {"enum_map": enum_map, "enum_inv": enum_inv})
                            best_cost = total_cost
            except: pass
            
            # Strategy 5: VALUE (Sparse Default)
            if len(vals) > 0:
                try:
                    # Only consider hashable values
                    hashable_vals = [v for v in vals if v is not None and not isinstance(v, (list, dict))]
                    value_counts = Counter(hashable_vals)
                    if value_counts:
                        most_common, count = value_counts.most_common(1)[0]
                        if count / len(vals) > 0.6:  # 60% threshold
                            cost = (len(vals) - count) * len(str(most_common))
                            if cost < best_cost:
                                best_strategy = ("VALUE", None, {"default": most_common})
                                best_cost = cost
                except: pass
            
            # Strategy 6: DELTA (Differential)
            if len(nums) == len(vals) and len(vals) > 1:
                try:
                    # Calculate average diff length vs value length
                    diffs = [vals[i] - vals[i-1] for i in range(1, len(vals))]
                    avg_diff_len = sum(len(str(int(d))) for d in diffs) / len(diffs)
                    avg_val_len = sum(len(str(int(v))) for v in vals) / len(vals)
                    
                    if avg_diff_len < avg_val_len - 1:
                        cost = avg_diff_len * len(vals)
                        if cost < best_cost:
                            best_strategy = ("DELTA", vals[0], {})
                            best_cost = cost
                except: pass
            
            # Strategy 7: LIQUID
            if len(vals) > 0:
                try:
                    u = len(set(json.dumps(x) for x in vals))
                    if (u / len(vals)) < 0.5:
                        repeats = sum(1 for i in range(1, len(vals)) if vals[i] == vals[i-1])
                        cost = (len(vals) - repeats) * 5  # Rough estimate
                        if cost < best_cost:
                            best_strategy = ("LIQUID", None, {})
                            best_cost = cost
                except: pass
                
            state, param, extra = best_strategy
            col_defs[k] = {"state": state, "param": param, "vals": vals, **extra}
        return col_defs

    def _detect_pattern(self, vals):
        if not vals[0] or not vals[1]: return None
        m = re.search(r'(\d+)', vals[0])
        if not m: return None
        p, s = vals[0][:m.start()], vals[0][m.end():]
        try:
            start = int(m.group(1))
            step = int(re.search(r'(\d+)', vals[1]).group(1)) - start
            digits = len(m.group(1))
            tpl = f"{p}{{:0{digits}d}}{s}"
            for i, v in enumerate(vals[:5]):
                if v != tpl.format(start + i*step): return None
            return (tpl, start, step)
        except: return None

    def _encode_inline(self, data):
        lines = []
        for row in data:
            parts = [f"{k}:{self._pack_value(v)}" for k, v in row.items()]
            lines.append(SEPARATOR.join(parts))
        return "\n".join(lines)

    def _pack_value(self, val):
        if val is None: return "null"
        if isinstance(val, bool): return "T" if val else "F"
        if isinstance(val, (int, float)):
            s = str(val)
            return s[:-2] if s.endswith(".0") else s
        return self._pack_str(str(val))

    def _pack_str(self, s, force_quote=False):
        if not s: return '""'
        if not force_quote and self._safe_str_re.match(s) and s not in ["null", "T", "F"]: return s
        return json.dumps(s, separators=(',', ':'))

    def _flatten(self, d, parent_key='', sep='.'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict) and v:
                items.extend(self._flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

def encode(data, anchor_every=DEFAULT_ANCHOR_INTERVAL):
    return ZonEncoder(anchor_every).encode(data)
