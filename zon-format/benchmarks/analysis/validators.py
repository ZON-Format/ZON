#!/usr/bin/env python3
"""
Answer validators for LLM retrieval accuracy benchmarks.
"""

import re


def normalize_value(value):
    """
    Normalizes a value for comparison.
    
    Args:
        value: Value to normalize
        
    Returns:
        Normalized string or None
    """
    if value is None:
        return None
    
    str_val = str(value).strip().lower()
    
    if str_val == '':
        return None
    
    # Boolean normalization
    if str_val in ('true', 't', 'yes', '1'):
        return 'true'
    if str_val in ('false', 'f', 'no', '0'):
        return 'false'
    if str_val in ('null', 'none', 'nil'):
        return None
    
    num_match = re.search(r'[\d,]+\.?\d*', str_val)
    if num_match:
        cleaned = num_match.group(0).replace(',', '')
        try:
            num = float(cleaned)
            if 'k' in str_val:
                return str(num * 1000)
            return str(num)
        except ValueError:
            pass
    
    if re.match(r'^\d{4}-\d{2}-\d{2}', str_val):
        return str_val.split('t')[0]
    
    if ',' in str_val:
        return ','.join(sorted(s.strip() for s in str_val.split(',')))
    
    return str_val


def validate_answer(actual, expected, question_type='field'):
    """
    Validates if actual answer matches expected answer.
    
    Args:
        actual: LLM's answer
        expected: Expected answer
        question_type: Type of question (field, structure, etc.)
        
    Returns:
        True if answers match
    """
    normalized_actual = normalize_value(actual)
    normalized_expected = normalize_value(expected)
    
    # Both null
    if normalized_actual is None and normalized_expected is None:
        return True
    
    if normalized_actual is None or normalized_expected is None:
        return False
    
    if normalized_actual == normalized_expected:
        return True
    
    if question_type == 'structure':
        expected_parts = normalized_expected.split(',')
        actual_parts = normalized_actual.split(',')
        return all(part in actual_parts for part in expected_parts)
    
    try:
        actual_num = float(normalized_actual)
        expected_num = float(normalized_expected)
        return abs(actual_num - expected_num) < 0.01
    except ValueError:
        pass
    
    return False


def extract_answer(response):
    """
    Extracts answer from LLM response.
    
    Args:
        response: LLM response text
        
    Returns:
        Extracted answer string
    """
    if not response:
        return ''
    
    text = response.strip()
    
    # Try to extract structured answer
    patterns = [
        r'answer:\s*(.+)',
        r'the answer is:\s*(.+)',
        r'result:\s*(.+)',
        r'^(.+)$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return text


if __name__ == "__main__":
    print("🧪 Answer Validation Tests\n")
    print("=" * 60)
    
    tests = [
        {'actual': '50000', 'expected': '$50,000', 'should': True},
        {'actual': '50k', 'expected': '50000', 'should': True},
        {'actual': '95000.00', 'expected': '95000', 'should': True},
        {'actual': 'true', 'expected': 'True', 'should': True},
        {'actual': 'T', 'expected': 'true', 'should': True},
        {'actual': 'yes', 'expected': 'true', 'should': True},
        {'actual': 'false', 'expected': 'F', 'should': True},
        {'actual': 'Engineering', 'expected': 'engineering', 'should': True},
        {'actual': 'ALICE', 'expected': 'alice', 'should': True},
        {'actual': '2025-01-01', 'expected': '2025-01-01T00:00:00Z', 'should': True},
        {'actual': 'a,b,c', 'expected': 'c,a,b', 'should': True},
        {'actual': 'Engineering,Sales', 'expected': 'Sales,Engineering', 'should': True},
        {'actual': 'The answer is: 42', 'expected': '42', 'should': True},
        {'actual': 'Answer: Engineering', 'expected': 'engineering', 'should': True},
        {'actual': '100', 'expected': '200', 'should': False},
        {'actual': 'true', 'expected': 'false', 'should': False},
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(tests):
        extracted = extract_answer(test['actual'])
        result = validate_answer(extracted, test['expected'], 'field')
        success = result == test['should']
        
        if success:
            passed += 1
            print(f"✅ Test {i+1}: \"{test['actual']}\" == \"{test['expected']}\" → {result}")
        else:
            failed += 1
            print(f"❌ Test {i+1}: \"{test['actual']}\" == \"{test['expected']}\" → {result} (expected {test['should']})")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
