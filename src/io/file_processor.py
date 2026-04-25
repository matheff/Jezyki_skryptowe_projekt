from pathlib import Path
import os
from src.models.sale_record import SaleRecord
from src.models.product import Product
import datetime


class FileProcessor:
    def parse_sdf(self, path):
        sdf_file_path = Path(path)

        if not sdf_file_path.exists():
            raise FileNotFoundError
        
        dataset = {}
        products = {}
        transactions = []
        errors = []

        section = ""
        line_number = 0

        try:
            with open(path, "r", encoding="utf-8") as f:
                expected_order = ["DATASET", "PRODUCTS", "TRANSACTIONS"]
                index = 0
                for line in f:
                    line_number += 1
                    line = line.strip()

                    if line:
                        if (line == "---"):
                            continue

                        if line.startswith("#"):
                            new_section = line[1:]

                            if new_section != expected_order[index]:
                                raise SdfParseError(f"Linia {line_number}: oczekiwano {expected_order[index]}, a jest {new_section}")

                            section = new_section
                            index += 1
                            continue
                        
                        if (section == "DATASET"):
                            key, value = line.split(":", 1)
                            if (key in ["owner", "index", "created", "currency"]):
                                dataset[key.strip()] = value.strip()
                            else:
                                raise SdfParseError(f"Linia {line_number}: Błąd w sekcji #DATASET")

                        elif (section == "PRODUCTS"):
                            parts = line.split("|")
                            if len(parts) != 4:
                                raise SdfParseError(f"Linia {line_number}: Błąd w skecji #PRODUCTS")
                            
                            product_id = parts[0].strip()
                            name = parts[1].strip()
                            category = parts[2].strip()
                            try:
                                price = float(parts[3])
                            except ValueError:
                                raise SdfParseError(f"Linia {line_number}: niepoprawna cena")

                            products[product_id] = Product(
                                                            product_id, 
                                                            name, 
                                                            category, 
                                                            price
                                                            )
                            
                        elif (section == "TRANSACTIONS"):
                            parts = line.split("|")

                            if len(parts) != 5:
                                errors.append(f"Linia {line_number}: brakujące pole")
                                continue

                            date, product_id, quantity, seller, region_code = parts

                            product_id = product_id.strip()

                            try:
                                quantity = int(quantity)
                            except ValueError:
                                errors.append(f"Linia {line_number}: zły typ danych")
                                continue

                            if (region_code not in ["WA", "KR", "GD", "PO", "WR", 
                                                    "LO", "RZ", "BY", "ZG", "OP"]):
                                errors.append(f"Linia {line_number}: nieprawidłowy kod regionu")
                                continue

                            if (product_id not in products):
                                errors.append(f"Linia {line_number}: nieistniejący product_id")
                                continue

                            product = products[product_id]

                            try:
                                date = datetime.datetime.strptime(date.strip(), "%d.%m.%Y").date()
                            except:
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
        except PermissionError:    
            raise PermissionError("Permission Error: plik jest nie do oczytu")

        return { 
                    "dataset": dataset,
                    "products": products,
                    "transactions": transactions,
                    "errors": errors
                }
                
class SdfParseError(Exception):
    pass 
