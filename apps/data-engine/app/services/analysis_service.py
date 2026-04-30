import pandas as pd


class AnalysisService:
    def get_summary(self) -> dict:
        data = {
            "City": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"],
            "Sales": [100, 150, 120, 200],
        }
        df = pd.DataFrame(data)
        return {
            "summary": df.describe().to_dict(),
            "rows": data,
        }
