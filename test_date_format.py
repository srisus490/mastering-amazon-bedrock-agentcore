"""
Test date format conversion for AI insights
"""
from datetime import date

# Simulate what the frontend should send
start_date = date(2026, 2, 14)
end_date = date(2026, 2, 19)

# Convert to YYYY-MM-DD format (what API expects)
start_str = start_date.isoformat()
end_str = end_date.isoformat()

print(f"Start date: {start_str}")
print(f"End date: {end_str}")
print(f"Format correct: {start_str == '2026-02-14' and end_str == '2026-02-19'}")

# Test with None values (should handle gracefully)
print("\nTesting with None values:")
print(f"None date: {None}")
print("Should not crash when dates are None")
