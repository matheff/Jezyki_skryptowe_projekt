import datetime
import os
import json
from src.io.file_processor import FileProcessor, SdfParseError
from src.models.sale_record import SaleRecord
from src.models.sales_dataset import SalesDataset
from src.analysis.statistics import SaleStatistics
from src.models.product import Product
from src.io.raport_generator import RaportGenerator


class ConsoleApp:
    def __init__(self, raports_dir="data/raports"):
        self.raports_dir   = raports_dir
        self.raport_generator = RaportGenerator(self.raports_dir)
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
        try:
            self.dataset, self.sales_dataset, self.products, self.errors = fp.parse_sdf(path)

            print(f"\nWczytano: {len(self.sales_dataset)}")
            print(f"Błędy: {len(self.errors)}")

            if self.errors:
                for err in self.errors[:10]:
                    print(err)

                if len(self.errors) > 10:
                    print(f" i {len(self.errors) - 10} więcej")
        except FileNotFoundError:
            print("Błąd: Plik nie istnieje.")
        except PermissionError:
            print("Błąd: Brak uprawnień do odczytu pliku.")
        except SdfParseError as e:
            print(f"Błąd parsowania SDF: {e}")
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")

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

        try:
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

                if start > end:
                        print("Błąd: Data 'Od' nie może być późniejsza niż data 'Do'.")
                        return

                filtered = self.sales_dataset.filter_by_date_range(start, end)

            elif choice == "4":
                value = input("Kod regionu: ")
                filtered = self.sales_dataset.filter_by_region(value)

            else:
                print("Zła kategoria")
                return
        
        except ValueError:
            print("Błąd: Niepoprawny format daty!")
            print("Użyj formatu: DD.MM.RRRR (np. 15.03.2025)")
            return
        
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")
            return
        
        if len(filtered) == 0:
            print("Brak wyników")
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

        path = self.raport_generator.generate_txt(self.dataset, self.sales_dataset)

        print(f"\nRaport zapisany na ścieżce: {path}")

    def export_json(self):
        if not self.check_sales_dataset():
            return

        path = self.raport_generator.generate_json(self.dataset, self.sales_dataset)

        print(f"\nJSON zapisany na ścieżce: {path}")

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
        
        if len(self.sales_dataset) == 0:
            print("Brak danych do statystyk")
            return False
        return True
    
    def pln(self, value):
        return f"{value:,.2f}".replace(",", " ").replace(".", ",") + " PLN"

    def convert_to_percent(self, value, total):
        return f"{(value / total * 100):.1f}%" if total else "0.0%"