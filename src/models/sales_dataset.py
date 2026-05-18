from src.models.sale_record import SaleRecord
import datetime

class SalesDataset:
    def __init__(self, records=None):
        if records is None:
            self.__records = []
        else:
            self.__records = list(records)

    def filter_by_category(self, category):
        if not isinstance(category, str):
            raise ValueError("Kategoria musi być tekstem")

        if not category.strip():
            raise ValueError("Kategoria nie może być pusta")

        return SalesDataset([
            record for record in self.__records
            if record.product.category.lower() == category.lower()
        ])
    
    def filter_by_date_range(self, start_date, end_date):
        if not isinstance(start_date, datetime.date):
            raise ValueError("start_date musi być typu date")
        
        if not isinstance(end_date, datetime.date):
            raise ValueError("end_date musi być typu date")
        
        if start_date > end_date:
            raise ValueError(
                "Data początkowa nie może być późniejsza od końcowej"
            )

        return SalesDataset([
            record for record in self.__records
            if start_date <= record.date <= end_date
        ])

    def filter_by_seller(self, seller):
        if not isinstance(seller, str):
            raise ValueError("Sprzedawca musi być tekstem")

        if not seller.strip():
            raise ValueError("Sprzedawca nie może być pusty")
    
        return SalesDataset([
            record for record in self.__records
            if record.seller.lower() == seller.lower()
        ])

    def filter_by_region(self, region):
        if not isinstance(region, str):
            raise ValueError("Region musi być tekstem")

        if not region.strip():
           raise ValueError("Region nie może być pusty")

        if region.upper() not in SaleRecord.allowed_regions:
            raise ValueError(f"Niepoprawny kod regionu: {region}")

        return SalesDataset([
            record for record in self.__records
            if record.region_code.lower() == region.lower()
        ])
    
    def get_filtered_categories(self):
        return {record.product.category for record in self.__records}

    def get_filtered_sellers(self):
        return {record.seller for record in self.__records}
    
    def get_filtered_region_codes(self):
        return {record.region_code for record in self.__records}
    
    def get_date_range(self):
        if not self.__records:
            raise ValueError("Brak danych")
        
        dates = [record.date for record in self.__records]
        return min(dates), max(dates)

    def __len__(self):
        return len(self.__records)
    
    def __iter__(self):
        return iter(self.__records)
    
    def __contains__(self, item):
        return item in self.__records