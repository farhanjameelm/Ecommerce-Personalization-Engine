from models import Event, EventType
from datetime import datetime, timedelta
import random


class MockEventGenerator:
    """Generates mock ecommerce events for testing and simulation."""
    
    PRODUCTS = [
        ("prod_001", "Electronics", "Wireless Headphones"),
        ("prod_002", "Electronics", "Smart Watch"),
        ("prod_003", "Clothing", "Running Shoes"),
        ("prod_004", "Clothing", "Winter Jacket"),
        ("prod_005", "Home", "Coffee Maker"),
        ("prod_006", "Home", "Desk Lamp"),
        ("prod_007", "Electronics", "Laptop Stand"),
        ("prod_008", "Clothing", "Backpack"),
    ]
    
    PAGES = [
        "/home",
        "/products",
        "/products/electronics",
        "/products/clothing",
        "/products/home",
        "/sale",
        "/promotions",
        "/about",
    ]
    
    COUPONS = ["SAVE10", "WELCOME20", "SUMMER25", "FLASH50"]
    
    SEARCH_QUERIES = [
        "wireless headphones",
        "running shoes sale",
        "coffee maker discount",
        "laptop accessories",
        "winter jacket",
        "promo codes",
    ]
    
    @staticmethod
    def generate_event(session_id: str, event_type: EventType = None) -> dict:
        """Generate a random event for a session."""
        if event_type is None:
            event_type = random.choice(list(EventType))
        
        product_id, product_category, _ = random.choice(MockEventGenerator.PRODUCTS) if event_type in [
            EventType.PRODUCT_VIEW, EventType.ADD_TO_CART, EventType.COMPARE_PRODUCTS
        ] else (None, None, None)
        
        page_url = random.choice(MockEventGenerator.PAGES) if event_type in [
            EventType.PAGE_VIEW, EventType.VIEW_PROMO
        ] else None
        
        search_query = random.choice(MockEventGenerator.SEARCH_QUERIES) if event_type == EventType.SEARCH else None
        
        coupon_code = random.choice(MockEventGenerator.COUPONS) if event_type == EventType.APPLY_COUPON else None
        
        cart_value = random.uniform(50, 500) if event_type in [
            EventType.ADD_TO_CART, EventType.CART_VIEW, EventType.CHECKOUT_START
        ] else None
        
        return {
            "event_type": event_type.value,
            "session_id": session_id,
            "product_id": product_id,
            "product_category": product_category,
            "page_url": page_url,
            "search_query": search_query,
            "coupon_code": coupon_code,
            "cart_value": cart_value,
        }
    
    @staticmethod
    def generate_browser_sequence(session_id: str, count: int = 5) -> list[dict]:
        """Generate a sequence typical of a browser."""
        events = []
        for i in range(count):
            event_type = random.choice([EventType.PAGE_VIEW, EventType.PRODUCT_VIEW])
            events.append(MockEventGenerator.generate_event(session_id, event_type))
        return events
    
    @staticmethod
    def generate_comparer_sequence(session_id: str, count: int = 6) -> list[dict]:
        """Generate a sequence typical of a comparer."""
        events = []
        # View multiple products
        for i in range(4):
            events.append(MockEventGenerator.generate_event(session_id, EventType.PRODUCT_VIEW))
        # Use compare feature
        events.append(MockEventGenerator.generate_event(session_id, EventType.COMPARE_PRODUCTS))
        # View more products
        events.append(MockEventGenerator.generate_event(session_id, EventType.PRODUCT_VIEW))
        return events
    
    @staticmethod
    def generate_discount_seeker_sequence(session_id: str, count: int = 5) -> list[dict]:
        """Generate a sequence typical of a discount seeker."""
        events = []
        events.append(MockEventGenerator.generate_event(session_id, EventType.VIEW_PROMO))
        events.append(MockEventGenerator.generate_event(session_id, EventType.SEARCH))
        events.append(MockEventGenerator.generate_event(session_id, EventType.PRODUCT_VIEW))
        events.append(MockEventGenerator.generate_event(session_id, EventType.APPLY_COUPON))
        events.append(MockEventGenerator.generate_event(session_id, EventType.ADD_TO_CART))
        return events
    
    @staticmethod
    def generate_cart_abandoner_sequence(session_id: str, count: int = 5) -> list[dict]:
        """Generate a sequence typical of a cart abandoner."""
        events = []
        events.append(MockEventGenerator.generate_event(session_id, EventType.PRODUCT_VIEW))
        events.append(MockEventGenerator.generate_event(session_id, EventType.ADD_TO_CART))
        events.append(MockEventGenerator.generate_event(session_id, EventType.CART_VIEW))
        events.append(MockEventGenerator.generate_event(session_id, EventType.ADD_TO_CART))
        events.append(MockEventGenerator.generate_event(session_id, EventType.CART_VIEW))
        return events
    
    @staticmethod
    def generate_loyal_customer_sequence(session_id: str, count: int = 4) -> list[dict]:
        """Generate a sequence typical of a loyal customer."""
        events = []
        events.append(MockEventGenerator.generate_event(session_id, EventType.LOGIN))
        events.append(MockEventGenerator.generate_event(session_id, EventType.PRODUCT_VIEW))
        events.append(MockEventGenerator.generate_event(session_id, EventType.ADD_TO_CART))
        events.append(MockEventGenerator.generate_event(session_id, EventType.PURCHASE))
        return events
