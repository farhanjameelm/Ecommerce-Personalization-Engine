from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    PAGE_VIEW = "page_view"
    PRODUCT_VIEW = "product_view"
    SEARCH = "search"
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"
    CART_VIEW = "cart_view"
    CHECKOUT_START = "checkout_start"
    CHECKOUT_COMPLETE = "checkout_complete"
    APPLY_COUPON = "apply_coupon"
    VIEW_PROMO = "view_promo"
    COMPARE_PRODUCTS = "compare_products"
    LOGIN = "login"
    PURCHASE = "purchase"


class ShopperState(str, Enum):
    BROWSER = "browser"
    COMPARER = "comparer"
    DISCOUNT_SEEKER = "discount_seeker"
    CART_ABANDONER = "cart_abandoner"
    LOYAL_CUSTOMER = "loyal_customer"


class Event(BaseModel):
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    product_id: Optional[str] = None
    product_category: Optional[str] = None
    page_url: Optional[str] = None
    search_query: Optional[str] = None
    cart_value: Optional[float] = None
    coupon_code: Optional[str] = None
    session_id: str


class Evidence(BaseModel):
    description: str
    weight: float  # 0-1, how strong this evidence is
    event_count: int


class ClassificationResult(BaseModel):
    state: ShopperState
    confidence: float  # 0-1
    evidence: List[Evidence]
    recommended_action: str
    recommended_nudge: str


class Session(BaseModel):
    session_id: str
    events: List[Event]
    classification: Optional[ClassificationResult] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
