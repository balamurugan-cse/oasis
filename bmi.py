from __future__ import annotations

import argparse
import sys

MAX_WEIGHT_KG = 500.0
MAX_HEIGHT_M = 3.0


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    return weight_kg / (height_m * height_m)


def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal weight"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def validate(weight_kg: float, height_m: float) -> None:
    if weight_kg <= 0 or height_m <= 0:
        raise ValueError("Weight and height must be greater than zero.")
    if weight_kg > MAX_WEIGHT_KG or height_m > MAX_HEIGHT_M:
        raise ValueError(
            "Please enter realistic values "
            f"(weight up to {MAX_WEIGHT_KG:.0f} kg, height up to {MAX_HEIGHT_M:.0f} m)."
        )


def prompt_float(label: str) -> float:
    while True:
        raw = input(f"Enter your {label}: ").strip()
        try:
            return float(raw)
        except ValueError:
            print(f"'{raw}' is not a valid number. Please try again.")


def report(weight_kg: float, height_m: float) -> None:
    bmi = calculate_bmi(weight_kg, height_m)
    category = classify_bmi(bmi)
    print(f"\nBMI: {bmi:.2f}")
    print(f"Category: {category}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate Body Mass Index (BMI).")
    parser.add_argument("--weight", type=float, help="Weight in kilograms")
    parser.add_argument("--height", type=float, help="Height in meters")
    args = parser.parse_args()

    weight_kg = args.weight if args.weight is not None else prompt_float("weight in kilograms")
    height_m = args.height if args.height is not None else prompt_float("height in meters")

    try:
        validate(weight_kg, height_m)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    report(weight_kg, height_m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
