import pandas as pd

data = [
    {
        "Date": "2026-03-01 00:00:00",
        "Day": "శని",
        "Lunar_Month": "ఫాల్గుణ",
        "Paksha": "శుద్ధ",
        "Thithi": "ఏకాదశి",
        "Thithi_End": "10:00:00",
        "Nakshatram": "పుష్యమి",
        "Nakshatram_End": "11:00:00",
        "Varjyam_Time": "12:00 PM - 01:30 PM",
        "Durmuhurtham_1": "06:00 AM - 07:30 AM",
        "Durmuhurtham_2": "03:00 PM - 04:30 PM"
    }
]

df = pd.DataFrame(data)
try:
    df.to_excel("sample_panchang.xlsx", index=False)
    print("Sample Excel file created successfully.")
except ImportError as e:
    print(f"Error creating Excel: {e}")
    print("Please install openpyxl: pip install openpyxl")
except Exception as e:
    print(f"An error occurred: {e}")
