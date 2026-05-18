from pathlib import Path
from src.models.sale_record import SaleRecord
from src.models.product import Product
from src.models.sales_dataset import SalesDataset
import datetime

class SdfParseError(Exception):
    pass 

class FileProcessor:
    def parse_sdf(self, path):
        sdf_file_path = Path(path)

        if not sdf_file_path.exists():
            raise FileNotFoundError(f"Plik nie istnieje: {path}")
        
        dataset = {}
        products = {}
        transactions = []
        errors = []

        section = None
        line_number = 0

        try:
            with open(path, "r", encoding="utf-8") as f:
                expected_order = ["#DATASET", "#PRODUCTS", "#TRANSACTIONS"]
                index = 0
                for line in f:
                    line_number += 1
                    line = line.strip()

                    if line:

                        if (line == "---"):
                            continue

                        if line.startswith("#"):
                            if line in expected_order:
                                new_section = line

                                if index >= len(expected_order):
                                    raise SdfParseError(
                                        f"Linia {line_number}: zbyt wiele sekcji"
                                    )

                                if new_section != expected_order[index]:
                                    raise SdfParseError(f"Linia {line_number}: oczekiwano {expected_order[index]}, a jest {new_section}")

                                section = new_section
                                index += 1
                                continue
                            else:
                                continue

                        if not section:
                            raise SdfParseError(
                                f"Linia {line_number}: dane poza sekcją"
                            )
                        
                        if (section == "#DATASET"):
                            if ":" not in line:
                                raise SdfParseError(
                                    f"Linia {line_number}: niepoprawny format DATASET"
                                )
                            
                            key, value = line.split(":", 1)

                            key = key.strip()
                            value = value.strip()

                            if not value:
                                raise SdfParseError(
                                    f"Linia {line_number}: pusta wartość pola {key}"
                                )
                            
                            if key in dataset:
                                raise SdfParseError(
                                    f"Linia {line_number}: duplikat pola {key}"
                                )

                            if (key in ["owner", "index", "created", "currency"]):
                                if key.strip() == "created":
                                    try:
                                        datetime.datetime.strptime(
                                            value,
                                            "%d.%m.%Y"
                                        )
                                    except ValueError:
                                        raise SdfParseError(
                                            f"Linia {line_number}: niepoprawna data created"
                                        )
                                    
                                if key == "currency" and value != "PLN":
                                    raise SdfParseError(
                                        f"Linia {line_number}: nieobsługiwana waluta"
                                    )

                                dataset[key] = value
                            
                            else:
                                raise SdfParseError(f"Linia {line_number}: Błąd w sekcji #DATASET")

                        elif (section == "#PRODUCTS"):
                            parts = line.split("|")
                            if len(parts) != 4:
                                raise SdfParseError(f"Linia {line_number}: Błąd w sekcji #PRODUCTS")
                            
                            product_id = parts[0].strip()
                            name = parts[1].strip()
                            category = parts[2].strip()
                            try:
                                price = float(parts[3])
                            except ValueError:
                                raise SdfParseError(f"Linia {line_number}: niepoprawna cena")
                            
                            if product_id in products:
                                raise SdfParseError(
                                    f"Linia {line_number}: duplikat product_id"
                                )
                            
                            try:
                                product = Product(
                                                            product_id, 
                                                            name, 
                                                            category, 
                                                            price
                                                            )
                            except ValueError as e:
                                raise SdfParseError(
                                    f"Linia {line_number}: {e}"
                                )
                            
                            products[product_id] = product


                        elif (section == "#TRANSACTIONS"):
                            parts = line.split("|")

                            if len(parts) != 5:
                                errors.append(f"Linia {line_number}: brakujące pole")
                                continue

                            date, product_id, quantity, seller, region_code = parts

                            product_id = product_id.strip()

                            try:
                                quantity = int(quantity)
                            except ValueError:
                                errors.append(f"Linia {line_number}: niepoprawna ilość")
                                continue

                            if (product_id not in products):
                                errors.append(f"Linia {line_number}: nieistniejący product_id")
                                continue

                            product = products[product_id]

                            try:
                                date = datetime.datetime.strptime(date.strip(), "%d.%m.%Y").date()
                            except ValueError:
                                errors.append(f"Linia {line_number}: niezgodny format daty")
                                continue

                            try:
                                record = SaleRecord(
                                                    product,
                                                    quantity,
                                                    date,
                                                    seller,
                                                    region_code
                                                    )
                            except ValueError as e:
                                errors.append(f"Linia {line_number}: {e}")
                                continue

                            transactions.append(record)
                if index != len(expected_order):
                    raise SdfParseError("Brak wymaganych sekcji")
                
                required = {"owner", "index", "created", "currency"}

                missing = required - dataset.keys()

                if missing:
                    raise SdfParseError(
                        f"Brak pól DATASET: {', '.join(missing)}"
                    )
        except PermissionError:    
            raise PermissionError("Permission Error: plik jest nie do oczytu")

        return dataset, SalesDataset(transactions), products, errors
                

