import datetime
import os
import json
from src.io.file_processor import FileProcessor
from src.models.sale_record import SaleRecord
from src.models.sales_dataset import SalesDataset
from src.analysis.statistics import SaleStatistics
from src.models.product import Product


class ConsoleApp:
    def __init__(self, reports_dir="data/reports"):
        self.reports_dir   = reports_dir
        self.dataset       = None
        self.sales_dataset = None
        self.products      = None
        self.errors        = None

    def run(self):
        while True:
            self.print_menu()
            choice = input("Wybierz opcję: ")

            try:
                if choice == "1":
                    self.load_file()
                elif choice == "2":
                    self.show_statistics()
                elif choice == "3":
                    self.filter_menu()
                elif choice == "4":
                    self.generate_txt_report()
                elif choice == "5":
                    self.export_json()
                elif choice == "6":
                    self.show_info()
                elif choice == "0":
                    break
                else:
                    print("Nieprawidłowa opcja")
            except Exception as e:
                print(f"Błąd: {e}")

    def print_menu(self):
        if self.dataset:
            print(f"\nOwner: {self.dataset.get('owner', 'no_owner')} | Index: {self.dataset.get('index', 'no_index')}")
        else:
            print("\nBrak danych")

        print(f"Liczba rekordów: {len(self.sales_dataset) if self.sales_dataset is not None else 0}")

        print(
                """
                1. Wczytaj plik
                2. Statystyki
                3. Filtrowanie
                4. Raport TXT
                5. Eksport JSON
                6. Informacje o zbiorze
                0. Wyjście
                """
              )

    def load_file(self):
        path = input("Enter path to sdf file: ")

        fp = FileProcessor()
        data = fp.parse_sdf(path)

        self.dataset = data["dataset"]
        self.sales_dataset = SalesDataset(data["transactions"])
        self.products = data["products"]
        self.errors = data["errors"]

        print(f"\nWczytano: {len(data['transactions'])}")
        print(f"Błędy: {len(self.errors)}")

        if self.errors:
            for err in self.errors[:10]:
                print(err)

            if len(self.errors) > 10:
                print(f" i {len(self.errors) - 10} więcej")

    def show_statistics(self):
        if not self.check_sales_dataset():
            return

        stats = SaleStatistics(self.sales_dataset)

        total = stats.total_revenue()
        avg = stats.average_revenue()

        print("\nSTATYSTYKI:")
        print(f"Przychód: {self.pln(total)}")
        print(f"Liczba transakcji: {len(self.sales_dataset)}")
        print(f"Średnia: {self.pln(avg)}")
        print(f"Top sprzedawca: {stats.top_seller()}")
        print(f"Top miesiąc: {stats.top_month()}")

        print("\nKategorie:")
        for key, value in stats.revenue_by_category().items():
            print(f"{key}: {self.pln(value)} {self.convert_to_percent(value, total)}")

        print("\nRegiony:")
        for key, value in stats.revenue_by_region_code().items():
            print(f"{key}: {self.pln(value)} {self.convert_to_percent(value, total)}")

        print("\nTop produkty:")
        for key, value in stats.top_revenue_by_product():
            print(f"{key}: {self.pln(value)}")

    def filter_menu(self):
        if not self.check_sales_dataset():
            return
        
        print(""" 
              1.Kategoria
              2.Sprzedawca
              3.Data
              4.Region
              """)
        
        choice = input("Wybór: ")

        if choice == "1":
            value = input("Kategoria: ")
            filtered = self.sales_dataset.filter_by_category(value)

        elif choice == "2":
            value = input("Sprzedawca: ")
            filtered = self.sales_dataset.filter_by_seller(value)

        elif choice == "3":
            start = input("Od (DD.MM.RRRR): ")
            end = input("Do (DD.MM.RRRR): ")

            start = datetime.datetime.strptime(start, "%d.%m.%Y").date()
            end = datetime.datetime.strptime(end, "%d.%m.%Y").date()

            filtered = self.sales_dataset.filter_by_date_range(start, end)

        elif choice == "4":
            value = input("Kod regionu: ")
            filtered = self.sales_dataset.filter_by_region(value)

        else:
            print("Zła kategoria")
            return
        
        print("Wynik:")
        for f in filtered:
            print(f)

        stats = SaleStatistics(filtered)
        print(f"\nPrzychód: {self.pln(stats.total_revenue())}")
        print(f"\nLiczba transakcji: {len(filtered)}")
        print(f"\nŚredni przychód: {self.pln(stats.average_revenue())}")
        print(f"\nTop sprzedawca danej kategorii: {stats.top_seller()}")

    def generate_txt_report(self):
        if not self.check_sales_dataset():
            return
        
        stats = SaleStatistics(self.sales_dataset)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H%M%S")

        index = self.dataset.get("index", "no_index")
        filename = f"{index}_raport_{timestamp}.txt"

        path = os.path.join(self.reports_dir, filename)

        os.makedirs(self.reports_dir, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write("DATASET:\n")
            for key, value in self.dataset.items():
                f.write(f"{key}: {value}\n")
            
            f.write("\nSTATYSTYKI:\n")
            total = stats.total_revenue()
            avg = stats.average_revenue()

            f.write(f"Przychód: {self.pln(total)}\n")
            f.write(f"Liczba transakcji: {len(self.sales_dataset)}\n")
            f.write(f"Średnia: {self.pln(avg)}\n")
            f.write(f"Top sprzedawca: {stats.top_seller()}\n")
            f.write(f"Top miesiąc: {stats.top_month()}\n")

            f.write("\nPRZYCHÓD MIESIĘCZNY:\n")
            for key, value in stats.revenue_by_date().items():
                f.write(f"{key}: {self.pln(value)}\n")

            f.write("\nRANKING SPRZEDAWCÓW:\n")
            for key, value in stats.revenue_by_seller().items():
                f.write(f"{key}: {self.pln(value)}\n")

            f.write("\nRANKING REGIONÓW:\n")
            for key, value in stats.revenue_by_region_code().items():
                f.write(f"{key}: {self.pln(value)}\n")
            
            print(f"\nRaport zapisany na ściezce: {path}")

    def export_json(self):
        if not self.check_sales_dataset():
            return
        
        stats = SaleStatistics(self.sales_dataset)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H%M%S")

        index = self.dataset.get("index", "no_index")
        filename = f"{index}_export_{timestamp}.json"

        path = os.path.join(self.reports_dir, filename)

        os.makedirs(self.reports_dir, exist_ok=True)

        total = stats.total_revenue()
        avg = stats.average_revenue()

        statistics = {
            "total_revenue": total,
            "average_revenue": avg,
            "transactions_count": len(self.sales_dataset),
            "top_seller": stats.top_seller(),
            "top_month": stats.top_month(),
            "revenue_by_category": stats.revenue_by_category(),
            "revenue_by_region": stats.revenue_by_region_code(),
            "revenue_by_month": stats.revenue_by_date(),
            "top_products": [
                {"product": key, "revenue": value} for key, value in stats.top_revenue_by_product()
            ]
        }

        transactions = [record.to_dict() for record in self.sales_dataset]

        data = {
            "dataset": self.dataset,
            "statistics": statistics,
            "transactions": transactions
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nJson zapisany na ściezce: {path}")

    def show_info(self):
        if not self.check_sales_dataset():
            return
        
        print("\nInformacje")
        print(self.dataset)

        print(f"Liczba rekordów: {len(self.sales_dataset)}")
        print(f"Produkty: {len(self.products)}")

        print(f"Kategorie: {self.sales_dataset.get_filtered_categories()}")
        print(f"Sprzedawcy: {self.sales_dataset.get_filtered_sellers()}")
        print(f"Regiony: {self.sales_dataset.get_filtered_region_codes()}")

        start, end = self.sales_dataset.get_date_range()

        print(f"Zakres dat: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}")

    def check_sales_dataset(self):
        if not self.sales_dataset:
            print("Najpierw wczytaj dane")
            return False
        return True
    
    def pln(self, value):
        return f"{value:,.2f}".replace(",", " ").replace(".", ",") + " PLN"

    def convert_to_percent(self, value, total):
        return f"{(value / total * 100):.1f}%" if total else "0.0%"