import pytest
from evaluation.benchmarks.testgeneval.compute_readability import compute_readability

def test_readability_computation():
    # Simple Python code to test
    test_code = """
def hello_world():
    print("Hello, World!")
    return None
"""
    # Now we expect this to work and return a readability score
    score = compute_readability(test_code)
    
    # The score should be a float
    assert isinstance(score, float)
    
    # The score should be reasonable (based on the regression coefficients)
    # Most scores fall between 1 and 10
    assert 0 < score < 15