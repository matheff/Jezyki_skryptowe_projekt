import os
import json
import datetime
from src.analysis.statistics import SaleStatistics
from src.io.excel_exporter import ExcelExporter

class RaportGenerator:
    def __init__(self, reports_dir):
        self.reports_dir = reports_dir
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_txt(self, dataset, sales_dataset):
        stats = SaleStatistics(sales_dataset)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H%M%S")

        index = dataset.get("index", "no_index")
        filename = f"{index}_raport_{timestamp}.txt"
        path = os.path.join(self.reports_dir, filename)

        with open(path, "w", encoding="utf-8") as f:
            f.write("DATASET:\n")
            for key, value in dataset.items():
                f.write(f"{key}: {value}\n")

            f.write("\nSTATYSTYKI:\n")
            f.write(f"Liczba transakcji: {len(sales_dataset)}\n")
            f.write(f"Przychód: {stats.total_revenue()}\n")
            f.write(f"Średnia: {stats.average_revenue()}\n")
            f.write(f"Top sprzedawca: {stats.top_seller()}\n")
            f.write(f"Top miesiąc: {stats.top_month()}\n")

            self.write_dataset(f, "Kategorie", stats.revenue_by_category())
            self.write_dataset(f, "Regiony", stats.revenue_by_region_code())
            self.write_dataset(f, "Top produkty", stats.top_revenue_by_product())
            self.write_dataset(f, "Zestawieniemiesięczne", stats.revenue_by_date())

        return path

    def generate_json(self, dataset, sales_dataset):
        stats = SaleStatistics(sales_dataset)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H%M%S")

        index = dataset.get("index", "no_index")
        filename = f"{index}_export_{timestamp}.json"
        path = os.path.join(self.reports_dir, filename)

        data = {
            "dataset": dataset,
            "statistics": {
                "total_revenue": stats.total_revenue(),
                "average_revenue": stats.average_revenue(),
                "transactions_count": len(sales_dataset),
                "top_seller": stats.top_seller(),
                "top_month": stats.top_month(),
                "revenue_by_category": stats.revenue_by_category(),
                "revenue_by_region": stats.revenue_by_region_code(),
                "revenue_by_month": stats.revenue_by_date(),
                "top_products": [
                    {"product": k, "revenue": v}
                    for k, v in stats.top_revenue_by_product().items()
                ]
            },
            "transactions": [r.to_dict() for r in sales_dataset]
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return path

    def generate_excel(self, dataset, sales_dataset, products):
        stats = SaleStatistics(sales_dataset)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H%M%S")

        index = dataset.get("index", "no_index")
        filename = f"{index}_excel_{timestamp}.xlsx"
        path = os.path.join(self.reports_dir, filename)

        exporter = ExcelExporter()
        exporter.export(sales_dataset, stats, products, path)

        return path

    def write_dataset(self, f, name, dataset):
        f.write(f"\n{name}:\n")

        if isinstance(dataset, dict):
            items = dataset.items()
        else:
            items = dataset

        for k, v in items:
            f.write(f"{k}: {v}\n")