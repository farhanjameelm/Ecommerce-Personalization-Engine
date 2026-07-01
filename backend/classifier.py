from typing import List, Dict
from backend.models import Event, ShopperState, Evidence, ClassificationResult, EventType
from datetime import datetime, timedelta


class ShopperClassifier:
    """Rule-based classifier that determines shopper state from event patterns."""
    
    def __init__(self):
        self.rules = {
            ShopperState.BROWSER: self._classify_browser,
            ShopperState.COMPARER: self._classify_comparer,
            ShopperState.DISCOUNT_SEEKER: self._classify_discount_seeker,
            ShopperState.CART_ABANDONER: self._classify_cart_abandoner,
            ShopperState.LOYAL_CUSTOMER: self._classify_loyal_customer,
        }
    
    def classify(self, events: List[Event]) -> ClassificationResult:
        """Classify a shopper based on their event history."""
        if not events:
            return self._default_classification()
        
        # Calculate scores for each state
        scores = {}
        all_evidence = []
        
        for state, rule_func in self.rules.items():
            score, evidence = rule_func(events)
            scores[state] = score
            all_evidence.extend(evidence)
        
        # Find the highest scoring state
        best_state = max(scores, key=scores.get)
        confidence = scores[best_state]
        
        # Filter evidence for the best state
        best_evidence = [e for e in all_evidence if self._is_evidence_for_state(e, best_state)]
        
        # Get recommendations
        action, nudge = self._get_recommendations(best_state, best_evidence)
        
        return ClassificationResult(
            state=best_state,
            confidence=confidence,
            evidence=best_evidence,
            recommended_action=action,
            recommended_nudge=nudge
        )
    
    def _default_classification(self) -> ClassificationResult:
        return ClassificationResult(
            state=ShopperState.BROWSER,
            confidence=0.5,
            evidence=[Evidence(description="No events yet", weight=0.5, event_count=0)],
            recommended_action="Show homepage with featured products",
            recommended_nudge="Welcome! Browse our collection"
        )
    
    def _classify_browser(self, events: List[Event]) -> tuple[float, List[Evidence]]:
        """Browser: Mostly page views, minimal interaction."""
        evidence = []
        score = 0.0
        
        page_views = [e for e in events if e.event_type == EventType.PAGE_VIEW]
        product_views = [e for e in events if e.event_type == EventType.PRODUCT_VIEW]
        
        if len(page_views) >= 3 and len(product_views) <= 2:
            evidence.append(Evidence(
                description=f"Viewed {len(page_views)} pages with minimal product interest",
                weight=0.7,
                event_count=len(page_views)
            ))
            score += 0.7
        
        if len(product_views) == 0 and len(page_views) > 0:
            evidence.append(Evidence(
                description="Only browsing pages, not viewing products",
                weight=0.8,
                event_count=len(page_views)
            ))
            score += 0.8
        
        # Check if no strong signals for other states
        cart_actions = [e for e in events if e.event_type in [EventType.ADD_TO_CART, EventType.CART_VIEW]]
        if len(cart_actions) == 0 and len(page_views) > 0:
            evidence.append(Evidence(
                description="No cart activity detected",
                weight=0.6,
                event_count=0
            ))
            score += 0.6
        
        return min(score, 1.0), evidence
    
    def _classify_comparer(self, events: List[Event]) -> tuple[float, List[Evidence]]:
        """Comparer: Views multiple products, compares similar items."""
        evidence = []
        score = 0.0
        
        product_views = [e for e in events if e.event_type == EventType.PRODUCT_VIEW]
        compare_events = [e for e in events if e.event_type == EventType.COMPARE_PRODUCTS]
        
        # Check for multiple product views
        unique_products = set(e.product_id for e in product_views if e.product_id)
        if len(unique_products) >= 3:
            evidence.append(Evidence(
                description=f"Viewed {len(unique_products)} different products",
                weight=0.6,
                event_count=len(unique_products)
            ))
            score += 0.6
        
        # Check for explicit compare events
        if len(compare_events) > 0:
            evidence.append(Evidence(
                description=f"Used compare feature {len(compare_events)} times",
                weight=0.9,
                event_count=len(compare_events)
            ))
            score += 0.9
        
        # Check for viewing same category multiple times
        categories = [e.product_category for e in product_views if e.product_category]
        if len(set(categories)) <= 2 and len(categories) >= 3:
            evidence.append(Evidence(
                description=f"Focused on {len(set(categories))} category(ies) with multiple views",
                weight=0.7,
                event_count=len(categories)
            ))
            score += 0.7
        
        # Check for back-and-forth behavior (viewing similar products)
        if len(product_views) >= 4:
            evidence.append(Evidence(
                description="Multiple product views indicating comparison behavior",
                weight=0.5,
                event_count=len(product_views)
            ))
            score += 0.5
        
        return min(score, 1.0), evidence
    
    def _classify_discount_seeker(self, events: List[Event]) -> tuple[float, List[Evidence]]:
        """Discount Seeker: Looks for promos, applies coupons, views sale pages."""
        evidence = []
        score = 0.0
        
        coupon_events = [e for e in events if e.event_type == EventType.APPLY_COUPON]
        promo_views = [e for e in events if e.event_type == EventType.VIEW_PROMO]
        search_promo = [e for e in events if e.event_type == EventType.SEARCH and e.search_query and 'promo' in e.search_query.lower()]
        
        if len(coupon_events) > 0:
            evidence.append(Evidence(
                description=f"Applied {len(coupon_events)} coupon(s)",
                weight=0.9,
                event_count=len(coupon_events)
            ))
            score += 0.9
        
        if len(promo_views) > 0:
            evidence.append(Evidence(
                description=f"Viewed {len(promo_views)} promotional pages",
                weight=0.8,
                event_count=len(promo_views)
            ))
            score += 0.8
        
        if len(search_promo) > 0:
            evidence.append(Evidence(
                description="Searched for promotional terms",
                weight=0.85,
                event_count=len(search_promo)
            ))
            score += 0.85
        
        # Check for sale page views
        sale_pages = [e for e in events if e.page_url and ('sale' in e.page_url.lower() or 'discount' in e.page_url.lower())]
        if len(sale_pages) > 0:
            evidence.append(Evidence(
                description=f"Visited {len(sale_pages)} sale/discount pages",
                weight=0.75,
                event_count=len(sale_pages)
            ))
            score += 0.75
        
        return min(score, 1.0), evidence
    
    def _classify_cart_abandoner(self, events: List[Event]) -> tuple[float, List[Evidence]]:
        """Cart Abandoner: Adds to cart but doesn't complete checkout."""
        evidence = []
        score = 0.0
        
        add_to_cart = [e for e in events if e.event_type == EventType.ADD_TO_CART]
        checkout_start = [e for e in events if e.event_type == EventType.CHECKOUT_START]
        checkout_complete = [e for e in events if e.event_type == EventType.CHECKOUT_COMPLETE]
        cart_views = [e for e in events if e.event_type == EventType.CART_VIEW]
        
        # Strong signal: added to cart but no checkout
        if len(add_to_cart) > 0 and len(checkout_start) == 0 and len(checkout_complete) == 0:
            evidence.append(Evidence(
                description=f"Added {len(add_to_cart)} item(s) to cart without starting checkout",
                weight=0.95,
                event_count=len(add_to_cart)
            ))
            score += 0.95
        
        # Started checkout but didn't complete
        if len(checkout_start) > 0 and len(checkout_complete) == 0:
            time_diff = self._get_time_since_last_event(events, EventType.CHECKOUT_START)
            if time_diff and time_diff > timedelta(minutes=30):
                evidence.append(Evidence(
                    description=f"Started checkout {int(time_diff.total_seconds() / 60)} minutes ago but didn't complete",
                    weight=0.9,
                    event_count=len(checkout_start)
                ))
                score += 0.9
        
        # Multiple cart views without action
        if len(cart_views) >= 3 and len(checkout_start) == 0:
            evidence.append(Evidence(
                description=f"Viewed cart {len(cart_views)} times without checkout",
                weight=0.7,
                event_count=len(cart_views)
            ))
            score += 0.7
        
        # Removed items from cart
        remove_from_cart = [e for e in events if e.event_type == EventType.REMOVE_FROM_CART]
        if len(remove_from_cart) > 0:
            evidence.append(Evidence(
                description=f"Removed {len(remove_from_cart)} item(s) from cart",
                weight=0.5,
                event_count=len(remove_from_cart)
            ))
            score += 0.5
        
        return min(score, 1.0), evidence
    
    def _classify_loyal_customer(self, events: List[Event]) -> tuple[float, List[Evidence]]:
        """Loyal Customer: Multiple purchases, logged in, returns to site."""
        evidence = []
        score = 0.0
        
        purchases = [e for e in events if e.event_type == EventType.PURCHASE]
        logins = [e for e in events if e.event_type == EventType.LOGIN]
        
        if len(purchases) >= 2:
            evidence.append(Evidence(
                description=f"Made {len(purchases)} purchase(s) in this session",
                weight=0.95,
                event_count=len(purchases)
            ))
            score += 0.95
        
        if len(purchases) == 1:
            evidence.append(Evidence(
                description="Completed a purchase",
                weight=0.7,
                event_count=1
            ))
            score += 0.7
        
        if len(logins) > 0:
            evidence.append(Evidence(
                description="Logged in to account",
                weight=0.6,
                event_count=len(logins)
            ))
            score += 0.6
        
        # Check for quick purchase behavior (low browsing, high conversion)
        product_views = [e for e in events if e.event_type == EventType.PRODUCT_VIEW]
        if len(purchases) > 0 and len(product_views) <= 2:
            evidence.append(Evidence(
                description="Quick purchase with minimal browsing",
                weight=0.8,
                event_count=len(product_views)
            ))
            score += 0.8
        
        return min(score, 1.0), evidence
    
    def _get_time_since_last_event(self, events: List[Event], event_type: EventType) -> timedelta:
        """Get time elapsed since the last event of a given type."""
        matching_events = [e for e in events if e.event_type == event_type]
        if not matching_events:
            return None
        
        last_event = max(matching_events, key=lambda e: e.timestamp)
        return datetime.utcnow() - last_event.timestamp
    
    def _is_evidence_for_state(self, evidence: Evidence, state: ShopperState) -> bool:
        """Determine if evidence is relevant to a given state."""
        # Simple heuristic: evidence with higher weight is more relevant
        # In a real system, this would be more sophisticated
        return evidence.weight > 0.5
    
    def _get_recommendations(self, state: ShopperState, evidence: List[Evidence]) -> tuple[str, str]:
        """Get action and nudge recommendations based on state."""
        recommendations = {
            ShopperState.BROWSER: (
                "Show personalized product recommendations based on browsing",
                "Discover products tailored to your interests"
            ),
            ShopperState.COMPARER: (
                "Display comparison table with key features and prices",
                "Compare these products side by side"
            ),
            ShopperState.DISCOUNT_SEEKER: (
                "Highlight available promotions and bundle deals",
                "Don't miss these limited-time offers!"
            ),
            ShopperState.CART_ABANDONER: (
                "Show cart summary with urgency messaging and free shipping threshold",
                "Complete your purchase now - items may sell out!"
            ),
            ShopperState.LOYAL_CUSTOMER: (
                "Show exclusive loyalty rewards and personalized re-order suggestions",
                "Welcome back! Here's your exclusive reward"
            ),
        }
        return recommendations.get(state, ("Show general recommendations", "Continue shopping"))
