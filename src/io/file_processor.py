from pathlib import Path
from src.models.sale_record import SaleRecord
from src.models.product import Product
from src.models.sales_dataset import SalesDataset
import datetime
import re

RE_SEPARATOR = re.compile(r"^---$")
RE_HEADER_FIELD = re.compile(r"^(?P<key>[a-z]+):\s*(?P<value>.*)$", re.IGNORECASE)
RE_SECTION = re.compile(r"^(?P<section>#DATASET|#PRODUCTS|#TRANSACTIONS)$")
RE_DATE = re.compile(r"^(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4})$")
RE_PRODUCT_LINE = re.compile(r"^(?P<id>[A-Za-z0-9]{4,10})\|(?P<name>[^|]+)\|(?P<category>[^|]+)\|(?P<price>\d+(?:\.\d{1,2})?)$", re.IGNORECASE)
RE_TRANSACTION_LINE = re.compile(r"""^
                                    (?P<date>\d{2}\.\d{2}\.\d{4})\|
                                    (?P<pid>[A-Za-z0-9]{4,10})\|
                                    (?P<qty>-?\d+)\| #Minus jest po to aby przy ujemnych wartościach nie zwracało błędu o niepoprawnym formacie, lecz o niepoprawnej ilości
                                    (?P<seller>[^|]+)\|
                                    (?P<region>[A-Z]{2})
                                $""", re.VERBOSE | re.IGNORECASE) #tu zamiast re.IGNORECASE też można użyć re.I to jest to samo

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

                    if not line:
                        continue

                    if RE_SEPARATOR.match(line):
                        continue

                    # match - match checks for a pattern only at the very beginning
                    # finditer - scans through the entire string and returns an iterator of match objects (Highly memory-efficient for large texts)
                    # search - zwraca pierwszy match który znajdzie

                    section_match = RE_SECTION.match(line) 

                    if section_match:
                        new_section = section_match.group("section") # da się łączyć grupy przez w tym przypadku section_match.sub(r'\2\3', jakiś_string)

                        if index >= len(expected_order):
                            raise SdfParseError(
                                f"Linia {line_number}: zbyt wiele sekcji"
                            )

                        if new_section != expected_order[index]:
                            raise SdfParseError(f"Linia {line_number}: oczekiwano {expected_order[index]}, a jest {new_section}")

                        section = new_section
                        index += 1
                        continue

                    if not section:
                        raise SdfParseError(
                            f"Linia {line_number}: dane poza sekcją"
                        )
                    
                    if (section == "#DATASET"):
                        match_header = RE_HEADER_FIELD.match(line)
                        if not match_header:
                            raise SdfParseError(
                                f"Linia {line_number}: niepoprawny format DATASET"
                            )
                        key = match_header.group("key")
                        value = match_header.group("value")

                        if not value.strip():
                            raise SdfParseError(
                                f"Linia {line_number}: pusta wartość pola {key}"
                            )
                        
                        if key in dataset:
                            raise SdfParseError(
                                f"Linia {line_number}: duplikat pola {key}"
                            )

                        if (key in ["owner", "index", "created", "currency"]):
                            if key == "created":
                                if not self.validate_date(value):
                                    raise SdfParseError(
                                        f"Linia {line_number}: niepoprawna data created"
                                    )
                                
                            if key == "currency" and value.strip().upper() != "PLN":
                                raise SdfParseError(
                                    f"Linia {line_number}: nieobsługiwana waluta"
                                )

                            dataset[key] = value
                        
                        else:
                            raise SdfParseError(f"Linia {line_number}: Błąd w sekcji #DATASET")

                    elif (section == "#PRODUCTS"):
                        match_product = RE_PRODUCT_LINE.match(line)
                        if not match_product:
                            raise SdfParseError(
                                f"Linia {line_number}: Błąd w sekcji #PRODUCTS"
                            )
                        
                        product_id = match_product.group("id")
                        name = match_product.group("name")
                        category = match_product.group("category")
                        try:
                            price = float(match_product.group("price"))
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
                        match_transaction = RE_TRANSACTION_LINE.match(line)
                        if not match_transaction:
                            parts = line.split("|")
                            if len(parts) < 5:
                                errors.append(f"Linia {line_number}: brakujące pole")
                                continue
                            elif len(parts) >5:
                                errors.append(f"Linia {line_number}: zbyt wiele pól")
                                continue
                            else: 
                                errors.append(f"Linia {line_number}: niepoprawny format transakcji")
                                continue

                        date = match_transaction.group("date")
                        product_id = match_transaction.group("pid")
                        seller = match_transaction.group("seller")
                        region_code = match_transaction.group("region")

                        product_id = product_id.strip()

                        try:
                            quantity = int(match_transaction.group("qty"))
                        except ValueError:
                            errors.append(f"Linia {line_number}: niepoprawna ilość")
                            continue

                        if quantity < 1:
                            errors.append(f"Linia {line_number}: ujemna ilość")
                            continue
                            
                        if (product_id not in products):
                            errors.append(f"Linia {line_number}: nieistniejący product_id")
                            continue

                        product = products[product_id]

                        if not seller.strip():
                            errors.append(f"Linia {line_number}: pusty sprzedawca")
                            continue
                        
                        validated_date = self.validate_date(date)
                        if not validated_date:
                            errors.append (f"Linia {line_number}: niezgodny format daty")
                            continue

                        if region_code not in SaleRecord.allowed_regions:
                            errors.append(
                                f"Linia {line_number}: nieprawidłowy kod regionu"
                            )
                            continue

                        try:
                            record = SaleRecord(
                                                product,
                                                quantity,
                                                validated_date,
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
    
    def validate_date(self, date_str):
        match_date = RE_DATE.match(date_str)

        if not match_date:
            return None

        day = int(match_date.group("day"))
        month = int(match_date.group("month"))
        year = int(match_date.group("year"))

        if not (1 <= day <= 31):
            return None

        if not (1 <= month <= 12):
            return None

        if not (1000 <= year <= 9999):
            return None

        try:
            return datetime.datetime.strptime(
                date_str,
                "%d.%m.%Y"
            ).date()

        except ValueError:
            return None
