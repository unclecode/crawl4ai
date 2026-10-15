"""
Tests for PR #1932 - feature/ Add additional return data types to JsonCssExtractionStrategy using transform

Adds a feature to specify additional return value data types directly within the JsonCssExtractionStrategy schema.
Int, float, and bool data types can be specified using the "transform" key-pair of the extraction Schema.

"""

from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

def transform_result(value, transform) -> str | int | float | bool:
        
    strategy = JsonCssExtractionStrategy(schema={"key": "value"})

    return strategy._apply_transform(value, transform)


class TestExistingTransforms:
    """Regression tests for existing JsonElementExtractionStrategy transform operations."""

    def test_uppercase(self):
        assert transform_result("test", "uppercase") == "TEST"

    def test_lowercase(self):
        assert transform_result("TEST", "lowercase") == "test"

    def test_strip(self):
        assert transform_result(" test ", "strip") == "test"


class TestAddedTransforms:
    """Unit tests for added JsonElementExtractionStrategy transform operations."""

    def test_int(self):
        assert transform_result("0", "int") == 0

    def test_int_pos_round_up(self):
        assert transform_result("1.5", "int") == 2
    
    def test_int_pos_round_down(self):
        assert transform_result("1.4", "int") == 1

    def test_int_neg_round_up(self):
        assert transform_result("-1.5", "int") == -2
    
    def test_int_neg_round_down(self):
        assert transform_result("-1.4", "int") == -1

    def test_float(self):
        assert transform_result("3.1416", "float") == 3.1416

    def test_bool_true_upper(self):
        assert transform_result("TRUE", "bool") == True

    def test_bool_false_upper(self):
        assert transform_result("FALSE", "bool") == False

    def test_bool_true_lower(self):
        assert transform_result("true", "bool") == True

    def test_bool_false_lower(self):
        assert transform_result("false", "bool") == False
    
    def test_bool_one(self):
        assert transform_result("1", "bool") == True

    def test_bool_zero(self):
        assert transform_result("0", "bool") == False

    def test_bool_default(self):
        assert transform_result("Other", "bool") == False