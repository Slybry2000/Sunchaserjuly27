import csv
from pathlib import Path


def validate_csv(path: str) -> bool:
    required = [
        "id",
        "name",
        "lat",
        "lon",
        "elevation",
        "category",
        "state",
        "timezone",
    ]
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            for col in required:
                if col not in row or not row[col]:
                    print(f"Row {i}: missing {col}")
                    return False
            try:
                float(row["lat"])
                float(row["lon"])
                float(row["elevation"])
            except Exception as e:
                print(f"Row {i}: invalid number: {e}")
                return False
    print("Validation passed.")
    return True


if __name__ == "__main__":
    import sys

    path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else str(Path(__file__).parent.parent / "data" / "pnw.csv")
    )
    validate_csv(path)
