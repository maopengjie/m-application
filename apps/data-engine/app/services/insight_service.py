from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import logging

from app.services.product_service import ProductService
from app.services.alert_service import AlertService
from app.schemas.product import InsightEvent, InsightResponse

logger = logging.getLogger(__name__)

class InsightService:
    def __init__(self, product_service: ProductService, alert_service: AlertService):
        self.product_service = product_service
        self.alert_service = alert_service

    def get_aggregated_insights(self, db: Session, user_id: int) -> InsightResponse:
        events: List[InsightEvent] = []
        
        # 1. Process Alerts (Triggered or Near Target)
        alerts = self.alert_service.list_alerts(db, user_id)
        for alert in alerts:
            # Map ALERT_HIT
            if alert.status == "triggered":
                events.append(InsightEvent(
                    id=f"alert_hit_{alert.id}",
                    product_id=alert.sku.product_id,
                    sku_id=alert.sku_id,
                    event_type="ALERT_HIT",
                    priority=10,
                    title="监测点命中",
                    description=f"商品已降至您的目标价 ¥{alert.target_price}",
                    current_price=float(alert.triggered_price or alert.current_price or 0),
                    original_price=float(alert.sku.price),
                    diff_amount=float(alert.sku.price - (alert.triggered_price or 0)),
                    image=alert.sku.product.main_image,
                    platform=alert.sku.platform,
                    timestamp=alert.triggered_at or datetime.now(),
                    metadata={"alert_id": alert.id}
                ))
            
            # Map NEAR_TARGET
            elif alert.status == "monitoring":
                current = float(alert.current_price or alert.sku.price or 0)
                target = float(alert.target_price)
                if current > 0 and current <= target * 1.05:
                    events.append(InsightEvent(
                        id=f"alert_near_{alert.id}",
                        product_id=alert.sku.product_id,
                        sku_id=alert.sku_id,
                        event_type="NEAR_TARGET",
                        priority=7,
                        title="即将达到目标价",
                        description=f"当前价 ¥{current} 距离目标价仅差 {(current - target):.2f}",
                        current_price=current,
                        original_price=float(alert.sku.price),
                        image=alert.sku.product.main_image,
                        platform=alert.sku.platform,
                        timestamp=datetime.now(),
                        metadata={"target_price": target}
                    ))

        # 2. Process Follows (Price Drops, Hist Lows, Risk)
        follows = self.product_service.list_followed_products(db, user_id)
        for follow in follows:
            product = follow.product
            
            # Map HIST_LOW
            if follow.is_near_low:
                events.append(InsightEvent(
                    id=f"follow_low_{follow.id}",
                    product_id=follow.product_id,
                    event_type="HIST_LOW",
                    priority=9,
                    title="跌至历史低位",
                    description="该商品正处于有记录以来的最低价格区间，建议入手",
                    current_price=float(product.final_price or product.min_price or 0),
                    image=product.main_image,
                    timestamp=datetime.now(),
                    metadata={}
                ))
            
            # Map PRICE_DROP (Significant drop > 10%)
            elif follow.price_change_percent and follow.price_change_percent < -10:
                events.append(InsightEvent(
                    id=f"follow_drop_{follow.id}",
                    product_id=follow.product_id,
                    event_type="PRICE_DROP",
                    priority=8,
                    title="大幅降价异动",
                    description=f"追踪期内累计下调 {abs(follow.price_change_percent):.0f}%",
                    current_price=float(product.final_price or product.min_price or 0),
                    diff_percent=follow.price_change_percent,
                    image=product.main_image,
                    timestamp=datetime.now(),
                    metadata={}
                ))
            
            # Map RISK_CHANGE
            if follow.risk_status == "高风险":
                events.append(InsightEvent(
                    id=f"follow_risk_{follow.id}",
                    product_id=follow.product_id,
                    event_type="RISK_CHANGE",
                    priority=8,
                    title="监测到异常风险",
                    description="近期评价或价格策略出现大幅异动，建议谨慎购买",
                    current_price=float(product.final_price or product.min_price or 0),
                    image=product.main_image,
                    timestamp=datetime.now(),
                    metadata={}
                ))

        # Sort by priority descending, then timestamp descending
        events.sort(key=lambda x: (x.priority, x.timestamp), reverse=True)
        
        # Filter duplicates (e.g. same product hit multiple rules, pick highest priority)
        seen_products = set()
        unique_events = []
        for e in events:
            if e.product_id not in seen_products:
                unique_events.append(e)
                seen_products.add(e.product_id)
        
        summary = f"今日发现 {len(unique_events)} 条深度异动资讯"
        if any(e.priority >= 9 for e in unique_events):
            summary = f"🔥 发现 {sum(1 for e in unique_events if e.priority >= 9)} 个关键购买点"

        return InsightResponse(
            events=unique_events,
            total=len(unique_events),
            summary=summary
        )
