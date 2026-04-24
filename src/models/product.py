class Product:

    def __init__(self, product_id, name, category, unit_price):
        self.__product_id     = product_id
        self.__name           = name
        self.__category       = category
        self.unit_price       = unit_price

    @property
    def product_id(self):
        return self.__product_id
    
    @property
    def name(self):
        return self.__name
    
    @property
    def category(self):
        return self.__category

    @property
    def unit_price(self):
        return self.__unit_price

    @unit_price.setter
    def unit_price(self, price):
        if(price <= 0):
            raise ValueError(f"Wrong price value: {price}")
        
        self.__unit_price = price

    def apply_discount(self, percent):
        if(percent < 0 or percent > 100):
            raise ValueError(f"Wrong percentage value: {percent}")
        else:
            return self.__unit_price * (1 - percent/100)
        
    def __str__(self):
        return (f"[{self.__product_id}] {self.__name} ({self.__category}) - {self.__unit_price} PLN")
    
    def __eq__(self, other):
        if not isinstance(other, Product):
            return False
        return self.__product_id == other.__product_id