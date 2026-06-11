from datetime import datetime

class SaleStatistics:
    def __init__(self, dataset):
        self.dataset = dataset

    def total_revenue(self):
        total = 0
        for record in self.dataset:
            total += record.total_price()
        return total

    def average_revenue(self):
        if(len(self.dataset) == 0):
            raise ValueError(f"Nie ma rekordów")
        else:
            return self.total_revenue() / len(self.dataset)
        
    def group_by(self, by_key, sort_by="value"):
        result = {}

        for record in self.dataset:
            key = by_key(record)
            revenue = record.total_price()

            if key not in result:
                result[key] = 0
            
            result[key] += revenue
        if(sort_by == "value"):
            return dict(sorted(result.items(), key=lambda item: item[1], reverse=True))
        elif (sort_by == "key"):
            return dict(sorted(result.items(), key=lambda item: item[0]))
    
    def revenue_by_category(self):
        return self.group_by(lambda r: r.product.category)
    
    def revenue_by_seller(self):
        return self.group_by(lambda r: r.seller)
    
    def revenue_by_region_code(self):
        return self.group_by(lambda r: r.region_code)
    
    def revenue_by_date(self):
        return self.group_by(lambda r:  r.date.strftime("%Y-%m"), sort_by="key")
    
    def top_revenue_by_product(self, n=5):
        result = {}

        for record in self.dataset:
            key = record.product.name
            revenue = record.total_price()

            if key not in result:
                result[key] = 0
            
            result[key] += revenue

        sorted_items = sorted(result.items(), key=lambda item: item[1], reverse=True)[:n]

        return dict(sorted_items)

    def top_seller(self):
        seller = self.revenue_by_seller()
        return max(seller, key=seller.get)
    
    def top_month(self):
        month = self.revenue_by_date()
        return max(month, key=month.get)
    
    def transaction_count(self):
        count = 0
        for i in self.dataset:
            count += 1
        return count