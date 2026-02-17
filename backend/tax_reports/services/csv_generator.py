import csv
from pathlib import Path


class UnifiedTaxCSVGenerator:

    HEADERS = [
        "Р“РѕРґ",
        "РљРІР°СЂС‚Р°Р»",
        "РќР°Р·РІР°РЅРёРµ РѕСЂРіР°РЅРёР·Р°С†РёРё",
        "РРќРќ",
        "РћР±РѕСЂРѕС‚",
        "РЎС‚Р°РІРєР°",
        "РЎСѓРјРјР° РµРґРёРЅРѕРіРѕ РЅР°Р»РѕРіР°",
        "РЎРѕС†С„РѕРЅРґ",
        "РС‚РѕРіРѕ Рє РѕРїР»Р°С‚Рµ"
    ]

    def __init__(self, data):
        self.data = data

    def generate(self, file_path):
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open(mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(self.HEADERS)
            writer.writerow([
                self.data["year"],
                self.data["quarter"],
                self.data["organization_name"],
                self.data["inn"],
                str(self.data["turnover"]),
                str(self.data["rate"]),
                str(self.data["unified_tax"]),
                str(self.data["social_fund"]),
                str(self.data["total_payable"]),
            ])
