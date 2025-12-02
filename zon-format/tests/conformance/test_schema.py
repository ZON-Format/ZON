"""
Tests for ZON Schema Validation
"""


from zon import zon, validate, ZonResult, ZonIssue


class TestSchemaBasics:
    """Test basic schema types."""
    
    def test_string_schema_valid(self):
        """Test valid string schema validation."""
        schema = zon.string()
        result = schema.parse("hello")
        assert result.success is True
        assert result.data == "hello"
    
    def test_string_schema_invalid(self):
        """Test invalid string schema validation."""
        schema = zon.string()
        result = schema.parse(123)
        assert result.success is False
        assert "Expected string" in result.error
    
    def test_number_schema_valid_int(self):
        """Test valid integer number schema validation."""
        schema = zon.number()
        result = schema.parse(42)
        assert result.success is True
        assert result.data == 42
    
    def test_number_schema_valid_float(self):
        """Test valid float number schema validation."""
        schema = zon.number()
        result = schema.parse(3.14)
        assert result.success is True
        assert result.data == 3.14
    
    def test_number_schema_invalid(self):
        """Test invalid number schema validation."""
        schema = zon.number()
        result = schema.parse("42")
        assert result.success is False
        assert "Expected number" in result.error
    
    def test_boolean_schema_valid(self):
        """Test valid boolean schema validation."""
        schema = zon.boolean()
        result = schema.parse(True)
        assert result.success is True
        assert result.data is True
    
    def test_boolean_schema_invalid(self):
        """Test invalid boolean schema validation."""
        schema = zon.boolean()
        result = schema.parse(1)
        assert result.success is False
        assert "Expected boolean" in result.error
    
    def test_enum_schema_valid(self):
        """Test valid enum schema validation."""
        schema = zon.enum(['admin', 'user'])
        result = schema.parse('admin')
        assert result.success is True
        assert result.data == 'admin'
    
    def test_enum_schema_invalid(self):
        """Test invalid enum schema validation."""
        schema = zon.enum(['admin', 'user'])
        result = schema.parse('guest')
        assert result.success is False
        assert "Expected one of" in result.error


class TestArraySchema:
    """Test array schemas."""
    
    def test_array_of_strings_valid(self):
        """Test valid array of strings schema validation."""
        schema = zon.array(zon.string())
        result = validate(['a', 'b', 'c'], schema)
        assert result.success is True
        assert result.data == ['a', 'b', 'c']
    
    def test_array_of_strings_invalid(self):
        """Test invalid array of strings schema validation."""
        schema = zon.array(zon.string())
        result = validate(['a', 1, 'c'], schema)
        assert result.success is False
        assert "Expected string" in result.error
    
    def test_array_invalid_type(self):
        """Test invalid array type schema validation."""
        schema = zon.array(zon.string())
        result = validate("not an array", schema)
        assert result.success is False
        assert "Expected array" in result.error
    
    def test_empty_array(self):
        """Test empty array schema validation."""
        schema = zon.array(zon.number())
        result = validate([], schema)
        assert result.success is True
        assert result.data == []


class TestObjectSchema:
    """Test object schemas."""
    
    def test_simple_object_valid(self):
        """Test valid simple object schema validation."""
        schema = zon.object({
            'name': zon.string(),
            'age': zon.number()
        })
        result = validate({'name': 'Alice', 'age': 30}, schema)
        assert result.success is True
        assert result.data == {'name': 'Alice', 'age': 30}
    
    def test_object_missing_field(self):
        """Test object missing field schema validation."""
        schema = zon.object({
            'name': zon.string(),
            'age': zon.number()
        })
        result = validate({'name': 'Alice'}, schema)
        assert result.success is False
    
    def test_object_invalid_field_type(self):
        """Test object invalid field type schema validation."""
        schema = zon.object({
            'name': zon.string(),
            'age': zon.number()
        })
        result = validate({'name': 'Alice', 'age': 'thirty'}, schema)
        assert result.success is False
        assert "Expected number" in result.error
    
    def test_object_invalid_type(self):
        """Test object invalid type schema validation."""
        schema = zon.object({'name': zon.string()})
        result = validate([1, 2, 3], schema)
        assert result.success is False
        assert "Expected object" in result.error


class TestOptionalSchema:
    """Test optional schemas."""
    
    def test_optional_present(self):
        """Test optional field present schema validation."""
        schema = zon.object({
            'name': zon.string(),
            'age': zon.number().optional()
        })
        result = validate({'name': 'Alice', 'age': 30}, schema)
        assert result.success is True
        assert result.data == {'name': 'Alice', 'age': 30}
    
    def test_optional_missing(self):
        """Test optional field missing schema validation."""
        schema = zon.object({
            'name': zon.string(),
            'age': zon.number().optional()
        })
        result = validate({'name': 'Alice'}, schema)
        assert result.success is True
        assert result.data == {'name': 'Alice', 'age': None}
    
    def test_optional_null(self):
        """Test optional field null schema validation."""
        schema = zon.string().optional()
        result = validate(None, schema)
        assert result.success is True
        assert result.data is None


class TestDescribe:
    """Test describe modifier."""
    
    def test_describe_string(self):
        """Test describe modifier on string schema."""
        schema = zon.string().describe("User's full name")
        prompt = schema.to_prompt()
        assert "string" in prompt
        assert "User's full name" in prompt
    
    def test_describe_number(self):
        """Test describe modifier on number schema."""
        schema = zon.number().describe("Age in years")
        prompt = schema.to_prompt()
        assert "number" in prompt
        assert "Age in years" in prompt


class TestToPrompt:
    """Test prompt generation."""
    
    def test_simple_prompt(self):
        """Test simple prompt generation."""
        schema = zon.object({
            'name': zon.string().describe("Full name"),
            'role': zon.enum(['admin', 'user']).describe("Access level")
        })
        prompt = schema.to_prompt()
        assert "object:" in prompt
        assert "name: string" in prompt
        assert "Full name" in prompt
        assert "role: enum(admin, user)" in prompt
        assert "Access level" in prompt
    
    def test_nested_prompt(self):
        """Test nested prompt generation."""
        schema = zon.object({
            'users': zon.array(zon.object({
                'id': zon.number(),
                'name': zon.string()
            }))
        })
        prompt = schema.to_prompt()
        assert "array" in prompt
        assert "object" in prompt


class TestValidateWithZonString:
    """Test validation with ZON-encoded strings."""
    
    def test_validate_zon_string(self):
        """Test validation with ZON-encoded string."""
        zon_string = """
name:Alice
age:30
"""
        schema = zon.object({
            'name': zon.string(),
            'age': zon.number()
        })
        result = validate(zon_string, schema)
        assert result.success is True
        assert result.data['name'] == 'Alice'
        assert result.data['age'] == 30
    
    def test_validate_invalid_zon_string(self):
        """Test validation with invalid ZON-encoded string."""
        invalid_zon = "name:Alice\nage:"
        schema = zon.object({
            'name': zon.string(),
            'age': zon.number()
        })
        result = validate(invalid_zon, schema)


class TestComplexSchemas:
    """Test complex nested schemas."""
    
    def test_user_schema(self):
        """Test complex user schema validation."""
        user_schema = zon.object({
            'name': zon.string().describe("Full name"),
            'email': zon.string().describe("Email address"),
            'role': zon.enum(['admin', 'user', 'guest']).describe("Access level"),
            'active': zon.boolean(),
            'tags': zon.array(zon.string()).optional()
        })
        
        valid_user = {
            'name': 'Alice',
            'email': 'alice@example.com',
            'role': 'admin',
            'active': True,
            'tags': ['vip', 'beta']
        }
        
        result = validate(valid_user, user_schema)
        assert result.success is True
        assert result.data['name'] == 'Alice'
        assert result.data['role'] == 'admin'
        assert result.data['tags'] == ['vip', 'beta']
    
    def test_nested_object_schema(self):
        """Test complex nested object schema validation."""
        config_schema = zon.object({
            'database': zon.object({
                'host': zon.string(),
                'port': zon.number()
            }),
            'cache': zon.object({
                'ttl': zon.number(),
                'enabled': zon.boolean()
            }).optional()
        })
        
        valid_config = {
            'database': {'host': 'localhost', 'port': 5432}
        }
        
        result = validate(valid_config, config_schema)
        assert result.success is True
        assert result.data['database']['host'] == 'localhost'
        assert result.data['cache'] is None
