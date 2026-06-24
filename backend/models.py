from sqlalchemy import Column, Integer, String, Float
from database import Base

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    zomato_url = Column(String, primary_key=True, index=True)
    address = Column(String)
    name = Column(String, index=True)
    online_order = Column(String)
    book_table = Column(String)
    rate = Column(Float, index=True)
    votes = Column(Integer, index=True)
    phone = Column(String)
    location = Column(String, index=True)
    rest_type = Column(String)
    dish_liked = Column(String)
    cuisines = Column(String, index=True)
    cost_for_two = Column(Float, index=True)
    reviews_list = Column(String)
    menu_item = Column(String)
    listed_type = Column(String)
    listed_city = Column(String)
