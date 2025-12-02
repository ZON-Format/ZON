import unittest
from zon import zon, validate, encode

class TestSchemaValidation(unittest.TestCase):
    def test_string_validation(self):
        """Test string validation rules (email, url, length)."""
        schema = zon.string().email()
        self.assertTrue(schema.parse('test@example.com').success)
        self.assertFalse(schema.parse('not-an-email').success)

        schema = zon.string().url()
        self.assertTrue(schema.parse('https://example.com').success)
        self.assertFalse(schema.parse('not a url').success)

        schema = zon.string().min(3).max(10)
        self.assertTrue(schema.parse('hello').success)
        self.assertFalse(schema.parse('hi').success)
        self.assertFalse(schema.parse('this is too long').success)

    def test_number_validation(self):
        """Test number validation rules (positive, int, range)."""
        schema = zon.number().positive()
        self.assertTrue(schema.parse(5).success)
        self.assertFalse(schema.parse(-5).success)
        self.assertFalse(schema.parse(0).success)

        schema = zon.number().int()
        self.assertTrue(schema.parse(42).success)
        self.assertFalse(schema.parse(3.14).success)

        schema = zon.number().min(0).max(100)
        self.assertTrue(schema.parse(50).success)
        self.assertFalse(schema.parse(-1).success)
        self.assertFalse(schema.parse(101).success)

    def test_array_validation(self):
        """Test array validation rules (length, elements)."""
        schema = zon.array(zon.string()).min(1).max(5)
        self.assertTrue(schema.parse(['a', 'b', 'c']).success)
        self.assertFalse(schema.parse([]).success)
        self.assertFalse(schema.parse(['a', 'b', 'c', 'd', 'e', 'f']).success)

        schema = zon.array(zon.number().positive())
        self.assertTrue(schema.parse([1, 2, 3]).success)
        self.assertFalse(schema.parse([1, -2, 3]).success)

    def test_nullable_support(self):
        """Test nullable support."""
        schema = zon.string().nullable()
        self.assertTrue(schema.parse('hello').success)
        self.assertTrue(schema.parse(None).success)

    def test_complex_schema(self):
        """Test complex nested schema validation."""
        UserSchema = zon.object({
            'id': zon.number().int().positive(),
            'email': zon.string().email(),
            'age': zon.number().int().min(0).max(120),
            'tags': zon.array(zon.string()).max(10).optional(),
            'website': zon.string().url().optional(),
        })

        valid_user = {
            'id': 1,
            'email': 'alice@example.com',
            'age': 25,
            'tags': ['developer', 'typescript'],
            'website': 'https://alice.dev',
        }

        self.assertTrue(UserSchema.parse(valid_user).success)

        invalid_user = {
            'id': -1,
            'email': 'not-an-email',
            'age': 150,
        }

        self.assertFalse(UserSchema.parse(invalid_user).success)

    def test_integration_with_encode(self):
        """Test integration with ZON encoding."""
        schema = zon.array(zon.object({
            'id': zon.number().int().positive(),
            'name': zon.string().min(1),
        }))

        valid_data = [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'},
        ]

        result = schema.parse(valid_data)
        self.assertTrue(result.success)
        if result.success:
            encoded = encode(result.data)
            self.assertTrue(encoded)

        invalid_data = [
            {'id': -1, 'name': 'Alice'},
            {'id': 2, 'name': ''},
        ]

        self.assertFalse(schema.parse(invalid_data).success)

    def test_error_messages(self):
        """Test error message generation."""
        schema = zon.object({
            'users': zon.array(zon.object({
                'age': zon.number().min(0).max(120),
            })),
        })

        data = {
            'users': [
                {'age': 25},
                {'age': 150},
            ],
        }

        result = schema.parse(data)
        self.assertFalse(result.success)
        if not result.success:
            self.assertGreater(len(result.issues), 0)
            self.assertEqual(result.issues[0].path, ['users', 1, 'age'])

if __name__ == '__main__':
    unittest.main()
