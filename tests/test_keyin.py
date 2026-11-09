import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "UniStation"))
from unistation.keyin import parse_point


class ParsePointTests(unittest.TestCase):
    def test_absolute_signs_spacing_and_mixed_units(self):
        self.assertEqual(parse_point(" ABS   +.5 m ; -2 cm ; 5. mm  "),
                         (500.0, -20.0, 5.0))

    def test_relative_point_uses_and_does_not_mutate_base(self):
        base = [10.0, -20.0, 3.0]
        result = parse_point("rEl 5; -2 cm; .5 m", base)
        self.assertEqual(result, (15.0, -40.0, 503.0))
        self.assertEqual(base, [10.0, -20.0, 3.0])
        self.assertIsInstance(result, tuple)

    def test_relative_input_requires_a_base(self):
        with self.assertRaisesRegex(ValueError, "Сначала задайте абсолютную точку"):
            parse_point("rel 1; 2; 3")

    def test_invalid_grammar_is_rejected(self):
        invalid = (
            "10; 20; 30",                 # missing mode
            "abs10; 20; 30",              # prefix needs whitespace
            "abs 1; 2",                   # too few components
            "abs 1; 2; 3; 4",              # too many components
            "abs 1,5; 2; 3",              # decimal comma
            "abs 1e3; 2; 3",               # exponent
            "abs 1/2; 2; 3",               # fraction
            "abs 1+2; 2; 3",               # expression
            "abs NaN; 2; 3",
            "abs Infinity; 2; 3",
            "abs 1 inch; 2; 3",            # unknown unit
            "abs 1 MM; 2; 3",              # units are lower-case
            "abs 1; ; 3",
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_point(value)

    def test_text_length_is_limited(self):
        with self.assertRaisesRegex(ValueError, "4096"):
            parse_point(" " * 4097)

    def test_numeric_overflow_and_unit_scaling_are_rejected(self):
        huge_digits = "9" * 400
        scaled_overflow = "1" + ("0" * 306) + " m"
        for value in (f"abs {huge_digits}; 0; 0", f"abs {scaled_overflow}; 0; 0"):
            with self.subTest(value=value[:32]), self.assertRaises(ValueError):
                parse_point(value)

    def test_relative_addition_overflow_is_rejected(self):
        base = (1.7e308, 0.0, 0.0)
        with self.assertRaisesRegex(ValueError, "относительных координат"):
            parse_point("rel " + "17" + ("0" * 307) + "; 0; 0", base)

    def test_base_must_have_three_finite_values(self):
        invalid_bases = ((1, 2), (1, 2, 3, 4), (1, math.inf, 3),
                         (1, math.nan, 3), ("x", 2, 3))
        for base in invalid_bases:
            with self.subTest(base=base), self.assertRaisesRegex(ValueError, "База"):
                parse_point("rel 0; 0; 0", base)


if __name__ == "__main__":
    unittest.main()
