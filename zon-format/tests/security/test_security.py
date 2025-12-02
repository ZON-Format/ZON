"""
Security & Robustness Tests

Port of security.test.ts from the TypeScript implementation.
Tests prototype pollution prevention, DoS prevention, and circular reference detection.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import zon
from zon import ZonDecodeError, ZonEncodeError


class TestSecurity(unittest.TestCase):
    """Security & Robustness tests."""

    def test_reject_proto_keys(self):
        """Should reject __proto__ keys to prevent prototype pollution."""
        malicious = """
@data(1):id,__proto__.polluted
1,true
"""
        decoded = zon.decode(malicious)
        self.assertFalse(hasattr({}, 'polluted'))

    def test_reject_constructor_prototype_keys(self):
        """Should reject constructor.prototype keys."""
        malicious = """
@data(1):id,constructor.prototype.polluted
1,true
"""
        decoded = zon.decode(malicious)
        self.assertFalse(hasattr({}, 'polluted'))

    def test_deep_nesting_in_decoder(self):
        """Should throw on deep nesting in decoder."""
        depth = 150
        deep_zon = '[' * depth + ']' * depth
        
        with self.assertRaises(ZonDecodeError) as context:
            zon.decode(deep_zon)
        
        self.assertIn('Maximum nesting depth exceeded', str(context.exception))

    def test_circular_reference_in_encoder(self):
        """Should throw on circular reference in encoder."""
        circular = {'name': 'loop'}
        circular['self'] = circular

        with self.assertRaises(ZonEncodeError) as context:
            zon.encode(circular)
        
        self.assertIn('Circular reference detected', str(context.exception))

    def test_indirect_circular_reference(self):
        """Should throw on indirect circular reference."""
        a = {'name': 'a'}
        b = {'name': 'b'}
        a['next'] = b
        b['next'] = a

        with self.assertRaises(ZonEncodeError) as context:
            zon.encode(a)
        
        self.assertIn('Circular reference detected', str(context.exception))


if __name__ == '__main__':
    unittest.main()
