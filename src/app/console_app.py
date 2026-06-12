import datetime
import os
import json
from src.io.file_processor import FileProcessor, SdfParseError
from src.models.sale_record import SaleRecord
from src.models.sales_dataset import SalesDataset
from src.analysis.statistics import SaleStatistics
from src.models.product import Product
from src.io.raport_generator import RaportGenerator
from src.io.excel_exporter import ExcelExporter
from src.db.database import SalesDatabase


class ConsoleApp:
    def __init__(self, raports_dir="data/reports"):
        self.raports_dir      = raports_dir
        self.raport_generator = RaportGenerator(self.raports_dir)
        self.dataset          = None
        self.sales_dataset    = None
        self.products         = None
        self.errors           = None
        self.db               = SalesDatabase()

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
                    self.generate_export_json()
                elif choice == "6":
                    self.show_info()
                elif choice == "7":
                    self.generate_export_excel()
                elif choice == "8":
                    self.database_option()
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
                7. Eksport Excel
                8. Baza danych
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
        self.stats_printer(stats.revenue_by_category().items())

        print("\nRegiony:")
        self.stats_printer(stats.revenue_by_region_code().items())

        print("\nTop produkty:")
        self.stats_printer(stats.top_revenue_by_product().items())

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

                try:
                    filtered = self.sales_dataset.filter_by_date_range(start, end)
                except ValueError as e:
                    print(f"Błąd: {e}")
                    return

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

    def generate_export_json(self):
        if not self.check_sales_dataset():
            return

        path = self.raport_generator.generate_json(self.dataset, self.sales_dataset)

        print(f"\nJSON zapisany na ścieżce: {path}")
    
    def generate_export_excel(self):
        if not self.check_sales_dataset():
            return

        try:
            path = self.raport_generator.generate_excel(
                self.dataset,
                self.sales_dataset
            )

            print(f"\nExcel zapisany na ścieżce: {path}")

        except ImportError as e:
            print(e)

        except IOError as e:
            print(e)

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

    def database_option(self):
        hostname = 'localhost'
        database = 'skryptowe'
        username = 'postgres'
        pwd = '123'
        port_id = 5432

        while(True):
            if self.db.is_connected():
                print(f"[połączono: {hostname}/{database}]")
            else:
                print("[brak połączenia]")

            print(
                        """
                        a) Połącz z bazą
                        b) Utwórz schemat
                        c) Importuj dane
                        d) Zapytania analityczne
                        e) Usuń schemat
                        0) Powrót.
                        """
                )
            
            choice = input("Wybierz opcję: ")
            try:
                if choice == "a":
                    self.db.connect(hostname, port_id, database, username, pwd)

                    if self.db.is_connected():
                        print("Połączono z bazą")
                    else:
                        print("Brak połączenia")
                elif choice == "b":
                    if not self.db.is_connected():
                        print("Najpierw połącz z bazą")
                        continue

                    self.db.create_schema()
                    print("Schemat utworzony")
                elif choice == "c":
                    if not self.db.is_connected():
                        print("Najpierw połącz z bazą")
                        continue

                    if self.products is None:
                        print("Najpierw wczytaj dane")
                        continue

                    dataset = {
                                    "products": [
                                        {
                                            "product_id": p.product_id,
                                            "name": p.name,
                                            "category": p.category,
                                            "unit_price": p.unit_price
                                        }
                                        for p in self.products.values()
                                    ],
                                    "transactions": [
                                        {
                                            "date": t.date,
                                            "product_id": t.product.product_id,
                                            "quantity": t.quantity,
                                            "seller": t.seller,
                                            "region_code": t.region_code,
                                            "total_value": t.total_price()
                                        }
                                        for t in self.sales_dataset
                                    ]
                                }

                    inserted = self.db.import_dataset(dataset)
                    print(f"Zaimportowano {inserted} transakcji")
                elif choice == "d":
                    if not self.db.is_connected():
                        print("Najpierw połącz z bazą")
                        continue

                    print( 
                            """
                            1) Przychód wg kategorii
                            2) Top 5 sprzedawców
                            3) Podsumowanie miesięczne
                            4) Liczba transakcji w bazie
                            0) Powrót.
                            """
                         )
                    choice_query = input("Wybierz opcję: ")
                    if choice_query == "1":
                        self.stats_printer(self.db.get_revenue_by_category())
                    elif choice_query == "2":
                        self.stats_printer(self.db.get_top_sellers())
                    elif choice_query == "3":
                        self.stats_printer(self.db.get_monthly_summary())
                    elif choice_query == "4":
                        print(f"Liczba transakcji: {self.db.get_transaction_count()}")
                    elif choice_query == "0":
                        continue
                        
                elif choice == "e":
                    if not self.db.is_connected():
                        print("Najpierw połącz z bazą")
                        continue
                    
                    confirm = input("Napewno chcesz usunąć schemat? (wpisz tak)\n")
                    if confirm.lower() == "tak":
                        self.db.drop_schema()
                        print("Schemat usunięty")
                    else: 
                        print("Schemat nie został usunięty")
                elif choice == "0":
                    self.db.disconnect()
                    break
                else:
                    print("Nieprawidłowa opcja")
            except Exception as e:
                print(f"Błąd: {e}")

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
    
    def stats_printer(self, dataset):
        if isinstance(dataset, dict):
            items = dataset.items()
        else:
            items = dataset

        for k, v in items:
            print(f" {k}: {self.pln(v)}")