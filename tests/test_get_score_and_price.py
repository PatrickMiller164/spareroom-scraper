import pytest
from src.utils import normalise

@pytest.mark.parametrize(
    "input, expected",
    [
        (10, 1.25),
        (20, 1),
        (30, 0.75),
        (40, 0.5),
        (50, 0.25),
        (60, 0),
        (70, -0.25)
    ]
)
def test_params(input, expected):
    assert normalise(input, 20 , 60) == expected
