import json
import re
import csv
import io
from typing import List, Dict, Any
from .constants import *
from .exceptions import ZonDecodeError

class ZonDecoder:
    def decode(self, zon_str: str) -> List[Dict[str, Any]]:
        if not zon_str: return []
        lines = zon_str.strip().split('\n')
        if not lines[0].startswith(HEADER_PREFIX): return self._decode_inline(lines)

        parts = lines[0].split(SEPARATOR)
        dict_map = []
        headers = {}
        keys_order = []

        for p in parts:
            if p.startswith(DICT_MARKER):
                dict_map = list(csv.reader([p[len(DICT_MARKER):]]))[0]
            elif SCHEMA_START in p:
                inner = p[p.find(SCHEMA_START)+1 : p.rfind(SCHEMA_END)]
                cols = re.split(r',(?![^(]*\))', inner)
                for c in cols:
                    if ':' not in c: continue
                    k, v = c.split(':', 1)
                    keys_order.append(k)
                    headers[k] = self._parse_rule(v)

        decoded = []
        prev_vals = {k: None for k in keys_order}
        
        for line in lines[1:]:
            line = line.strip()
            if not line: continue

            if line.endswith(REPEAT_SUFFIX) and line[:-1].isdigit():
                count = int(line[:-1])
                for _ in range(count):
                    row = {}
                    curr = len(decoded)
                    for k in keys_order:
                        val = self._calc_val(headers[k], curr, prev_vals[k])
                        row[k] = val
                        prev_vals[k] = val
                    decoded.append(self._unflatten(row))
                continue

            clean = re.sub(r'^\$\d+:', '', line)
            is_anchor = line.startswith(ANCHOR_PREFIX)
            tokens = list(csv.reader([clean]))[0] if clean else []
            if len(tokens) < len(keys_order): tokens.extend([""] * (len(keys_order) - len(tokens)))

            row = {}
            curr = len(decoded)
            for idx, k in enumerate(keys_order):
                tok = tokens[idx]
                rule = headers[k]
                val = None
                
                if tok == "" and not is_anchor:
                    val = self._calc_val(rule, curr, prev_vals[k])
                elif tok.startswith(DICT_REF_PREFIX) and tok[1:].isdigit():
                    val = self._unpack(dict_map[int(tok[1:])])
                else:
                    val = self._unpack(tok)
                    
                    # Apply rule-specific transformations
                    if rule['type'] == 'MULT' and isinstance(val, (int, float)):
                        val = val / rule['factor']
                    elif rule['type'] == 'ENUM' and isinstance(val, int):
                        if 0 <= val < len(rule['enum_map']):
                            val = rule['enum_map'][val]
                    elif rule['type'] == 'DELTA' and isinstance(val, (int, float)) and curr > 0:
                        val = prev_vals[k] + val if prev_vals[k] is not None else rule['base'] + val
                
                row[k] = val
                prev_vals[k] = val
            decoded.append(self._unflatten(row))
        return decoded

    def _parse_rule(self, v):
        if v.startswith(RANGE_KEYWORD):
            p = v[len(RANGE_KEYWORD)+1:-1].split(',')
            return {'type': 'RANGE', 'start': float(p[0]), 'step': float(p[1])}
        if v.startswith(PATTERN_KEYWORD):
            args = v[len(PATTERN_KEYWORD)+1:-1]
            lc = args.rfind(',')
            slc = args.rfind(',', 0, lc)
            return {'type': 'PATTERN', 'tpl': args[:slc], 'start': int(args[slc+1:lc]), 'step': int(args[lc+1:])}
        if v.startswith(MULT_KEYWORD):
            return {'type': 'MULT', 'factor': float(v[len(MULT_KEYWORD)+1:-1])}
        if v.startswith(ENUM_KEYWORD):
            # E(val1,val2,...)
            inner = v[len(ENUM_KEYWORD)+1:-1]
            enum_vals = list(csv.reader([inner]))[0]
            enum_map = [self._unpack(ev) for ev in enum_vals]
            return {'type': 'ENUM', 'enum_map': enum_map}
        if v.startswith(VALUE_KEYWORD):
            # V(default)
            default_str = v[len(VALUE_KEYWORD)+1:-1]
            return {'type': 'VALUE', 'default': self._unpack(default_str)}
        if v.startswith(DELTA_KEYWORD):
            # Δ(base)
            base = float(v[len(DELTA_KEYWORD)+1:-1])
            return {'type': 'DELTA', 'base': base}
        if v == LIQUID_KEYWORD: 
            return {'type': 'LIQUID'}
        return {'type': 'SOLID'}

    def _calc_val(self, rule, idx, prev):
        if rule['type'] == 'RANGE': return rule['start'] + (idx * rule['step'])
        if rule['type'] == 'PATTERN': return rule['tpl'].format(rule['start'] + (idx * rule['step']))
        if rule['type'] == 'LIQUID': return prev
        if rule['type'] == 'VALUE': return rule['default']
        return prev

    def _unpack(self, val):
        if val == 'null': return None
        if val == 'T': return True
        if val == 'F': return False
        
        # Handle quoted strings (JSON format)
        if val.startswith('"') and val.endswith('"'):
            try:
                return json.loads(val)
            except: pass
        
        # Try numeric
        try: return int(val)
        except: pass
        try: return float(val)
        except: pass
        
        return val

    def _decode_inline(self, lines):
        res = []
        for l in lines:
            row = {}
            for p in l.split(SEPARATOR):
                if ':' in p:
                    k, v = p.split(':', 1)
                    row[k] = self._unpack(v)
            res.append(self._unflatten(row))
        return res

    def _unflatten(self, d, sep='.'):
        res = {}
        for k, v in d.items():
            p = k.split('.')
            t = res
            for x in p[:-1]:
                if x not in t:
                    t[x] = {}
                elif not isinstance(t[x], dict):
                    # If intermediate value is not a dict, skip this key
                    continue
                t = t[x]
            if isinstance(t, dict):  # Only assign if t is still a dict
                t[p[-1]] = v
        return res

def decode(data):
    return ZonDecoder().decode(data)
