import unittest
from zon import zon
from datetime import datetime

class TestSchemaPhase1(unittest.TestCase):
    def test_regex_pattern_validation(self):
        """Test regex pattern validation for strings."""
        schema = zon.string().regex(r'^[A-Z]{3}-\d{4}$')
        
        self.assertTrue(schema.parse('ABC-1234').success)
        self.assertFalse(schema.parse('abc-1234').success)
        
        invalid = schema.parse('abc-1234')
        if not invalid.success:
            self.assertIn('Pattern mismatch', invalid.error)

    def test_custom_error_message(self):
        """Test custom error messages for regex validation."""
        schema = zon.string().regex(r'^\d{3}-\d{2}-\d{4}$', 'Invalid SSN format')
        
        invalid = schema.parse('123-45-678')
        self.assertFalse(invalid.success)
        if not invalid.success:
            self.assertIn('Invalid SSN format', invalid.error)

    def test_uuid_validation(self):
        """Test UUID validation."""
        schema = zon.string().uuid()
        
        self.assertTrue(schema.parse('123e4567-e89b-12d3-a456-426614174000').success)
        self.assertFalse(schema.parse('not-a-uuid').success)

        schema_v4 = zon.string().uuid('v4')
        self.assertTrue(schema_v4.parse('123e4567-e89b-42d3-a456-426614174000').success)
        self.assertFalse(schema_v4.parse('123e4567-e89b-12d3-a456-426614174000').success)

    def test_datetime_validation(self):
        """Test ISO datetime validation."""
        schema = zon.string().datetime()
        
        self.assertTrue(schema.parse('2024-01-01T12:00:00Z').success)
        self.assertFalse(schema.parse('2024-01-01').success)

    def test_literal_values(self):
        """Test literal value validation."""
        schema = zon.literal('approved')
        self.assertTrue(schema.parse('approved').success)
        self.assertFalse(schema.parse('pending').success)

        schema_num = zon.literal(42)
        self.assertTrue(schema_num.parse(42).success)
        self.assertFalse(schema_num.parse(43).success)

    def test_union_types(self):
        """Test union type validation."""
        schema = zon.union(zon.string(), zon.number())
        self.assertTrue(schema.parse('hello').success)
        self.assertTrue(schema.parse(42).success)
        self.assertFalse(schema.parse(True).success)

        schema_complex = zon.union(
            zon.object({'type': zon.literal('text'), 'content': zon.string()}),
            zon.object({'type': zon.literal('number'), 'value': zon.number()})
        )
        self.assertTrue(schema_complex.parse({'type': 'text', 'content': 'hello'}).success)
        self.assertTrue(schema_complex.parse({'type': 'number', 'value': 42}).success)
        self.assertFalse(schema_complex.parse({'type': 'boolean', 'value': True}).success)

    def test_default_values(self):
        """Test default value handling."""
        schema = zon.string().default('unknown')
        
        result = schema.parse(None)
        self.assertTrue(result.success)
        self.assertEqual(result.data, 'unknown')

        result_valid = schema.parse('actual')
        self.assertTrue(result_valid.success)
        self.assertEqual(result_valid.data, 'actual')

    def test_custom_refinements(self):
        """Test custom refinement validation."""
        schema = zon.number().refine(lambda val: val % 2 == 0, 'Must be even')
        
        self.assertTrue(schema.parse(2).success)
        self.assertFalse(schema.parse(3).success)

    def test_date_time_types(self):
        """Test date and time specific validation."""
        schema_date = zon.string().date()
        self.assertTrue(schema_date.parse('2024-01-01').success)
        self.assertFalse(schema_date.parse('2024-01-01T12:00:00Z').success)

        schema_time = zon.string().time()
        self.assertTrue(schema_time.parse('12:30:45').success)
        self.assertTrue(schema_time.parse('23:59:59').success)
        self.assertFalse(schema_time.parse('12:30').success)
        self.assertFalse(schema_time.parse('2024-01-01T12:00:00Z').success)

    def test_boolean_literal(self):
        """Test boolean literal validation."""
        schema = zon.literal(True)
        self.assertTrue(schema.parse(True).success)
        self.assertFalse(schema.parse(False).success)
        self.assertFalse(schema.parse('true').success)

    def test_complex_defaults(self):
        """Test default values with complex types."""
        schema = zon.object({'name': zon.string()}).default({'name': 'Anonymous'})
        
        result = schema.parse(None)
        self.assertTrue(result.success)
        self.assertEqual(result.data, {'name': 'Anonymous'})

        schema_num = zon.number().default(0)
        self.assertTrue(schema_num.parse(None).success)
        self.assertEqual(schema_num.parse(None).data, 0)

    def test_cross_field_refinement(self):
        """Test validation across multiple fields."""
        schema = zon.object({
            'password': zon.string().min(8),
            'confirmPassword': zon.string()
        }).refine(
            lambda data: data['password'] == data['confirmPassword'],
            'Passwords must match'
        )
        
        self.assertTrue(schema.parse({'password': 'secret123', 'confirmPassword': 'secret123'}).success)
        
        result = schema.parse({'password': 'secret123', 'confirmPassword': 'different'})
        self.assertFalse(result.success)
        self.assertIn('Passwords must match', result.error)

    def test_combined_features(self):
        """Test combination of multiple validation features."""
        schema = zon.object({
            'orderId': zon.string().regex(r'^ORD-\d{6}$').describe('Order ID'),
            'status': zon.union(
                zon.literal('pending'),
                zon.literal('approved'),
                zon.literal('rejected')
            ),
            'amount': zon.number().positive().min(0),
            'customerId': zon.string().uuid().optional(),
            'createdAt': zon.string().datetime().default(datetime.now().isoformat()),
        }).refine(
            lambda data: data['status'] != 'approved' or data['amount'] > 0,
            'Approved orders must have positive amount'
        )

        valid = {
            'orderId': 'ORD-123456',
            'status': 'approved',
            'amount': 100,
            'customerId': '550e8400-e29b-41d4-a716-446655440000',
            'createdAt': '2024-01-01T12:00:00Z'
        }
        self.assertTrue(schema.parse(valid).success)

        schema_regex = zon.string().regex(r'^[A-Z]{3}$').default('ABC')
        self.assertEqual(schema_regex.parse(None).data, 'ABC')

        schema_union = zon.union(zon.string(), zon.number()).refine(lambda val: val != '', 'Cannot be empty')
        self.assertTrue(schema_union.parse('hello').success)
        self.assertFalse(schema_union.parse('').success)

    def test_to_prompt(self):
        """Test prompt generation from schema."""
        schema = zon.string().regex(r'^\d{3}$').default('000')
        prompt = schema.toPrompt()
        self.assertIn('pattern', prompt)
        self.assertIn('default', prompt)

    def test_example_method(self):
        """Test example() method on base schema."""
        schema = zon.string().example("test")
        self.assertEqual(schema._example_value, "test")
        self.assertTrue(schema.parse("test").success)

    def test_nullable_schema(self):
        """Test nullable() on base schema."""
        schema = zon.string().nullable()
        self.assertTrue(schema.parse(None).success)
        self.assertTrue(schema.parse("test").success)
        self.assertFalse(schema.parse(123).success)
        
        obj_schema = zon.object({'field': zon.number().nullable()})
        self.assertTrue(obj_schema.parse({'field': None}).success)
        self.assertTrue(obj_schema.parse({'field': 123}).success)
        self.assertFalse(obj_schema.parse({'field': "bad"}).success)

    def test_negative_number(self):
        """Test negative() validation."""
        schema = zon.number().negative()
        self.assertTrue(schema.parse(-1).success)
        self.assertTrue(schema.parse(-100.5).success)
        self.assertFalse(schema.parse(0).success)
        self.assertFalse(schema.parse(1).success)

if __name__ == '__main__':
    unittest.main()
