import datetime
from src.models.product import Product

class SaleRecord:
    def __init__(self, product, quantity, date, seller, region_code):
        self.__product      = product
        self.quantity       = quantity
        self.__date         = date
        self.__seller       = seller
        self.__region_code  = region_code

    @property
    def product(self):
        return self.__product
    
    @property
    def date(self):
        return self.__date
    
    @property
    def seller(self):
        return self.__seller
    
    @property
    def region_code(self):
        return self.__region_code
    
    @property
    def quantity(self):
        return self.__quantity

    @quantity.setter
    def quantity(self, quantity):
        if(quantity < 1):
            raise ValueError(f"Wrong quantity value: {quantity}")
        self.__quantity = quantity

    def total_price(self):
        return self.__quantity *  self.__product.unit_price
    
    def to_dict(self):
        return {
                "date": self.__date.isoformat(), 
                "product_id": self.__product.product_id, 
                "quantity": self.__quantity, 
                "seller": self.__seller, 
                "region_code": self.__region_code
               }

    def __str__(self):
        return (f"{self.__date} {self.__product.name} {self.__quantity} szt. {self.total_price()} PLN {self.__seller} {self.__region_code}")