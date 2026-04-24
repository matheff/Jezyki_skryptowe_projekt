from src.models.sale_record import SaleRecord

class SalesDataset:
    def __init__(self, records=None):
        if records is None:
            self.__records = []
        else:
            self.__records = list(records)

    def filter_by_category(self, category):
        return SalesDataset([
            record for record in self.__records
            if record.product.category.lower() == category.lower()
        ])
    
    def filter_by_date_range(self, start_date, end_date):
        return SalesDataset([
            record for record in self.__records
            if start_date <= record.date <= end_date
        ])

    def filter_by_seller(self, seller):
        return SalesDataset([
            record for record in self.__records
            if record.seller.lower() == seller.lower()
        ])

    def filter_by_region(self, region):
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
        dates = [record.date for record in self.__records]
        return min(dates), max(dates)

    def __len__(self):
        return len(self.__records)
    
    def __iter__(self):
        return iter(self.__records)
    
    def __contains__(self, item):
        return item in self.__records