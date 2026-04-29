from typing import List, Dict, Any
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from app.models.analytics import AnalyticsEvent
from datetime import datetime, timedelta

class AnalyticsRepository:
    def log_event(self, db: Session, event_name: str, user_id: int, properties: Dict[str, Any]) -> AnalyticsEvent:
        db_event = AnalyticsEvent(
            event_name=event_name,
            user_id=user_id,
            properties=properties
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event

    def get_summary_stats(self, db: Session, days: int = 7) -> Dict[str, Any]:
        since = datetime.now() - timedelta(days=days)
        query_expr = AnalyticsEvent.properties["q"].as_string()
        
        # Core counts
        counts = db.query(
            AnalyticsEvent.event_name,
            func.count(AnalyticsEvent.id)
        ).filter(
            AnalyticsEvent.created_at >= since
        ).group_by(
            AnalyticsEvent.event_name
        ).all()
        
        stats = {name: count for name, count in counts}
        
        # Funnel Calculation
        # Search -> Detail -> Buy
        search_count = stats.get("search_triggered", 0)
        detail_view_count = stats.get("product_detail_view", 0)
        buy_click_count = stats.get("buy_button_click", 0)
        alert_created_count = stats.get("alert_created", 0)
        
        funnel = {
            "search_to_detail": (detail_view_count / search_count * 100) if search_count > 0 else 0,
            "detail_to_buy": (buy_click_count / detail_view_count * 100) if detail_view_count > 0 else 0,
            "detail_to_alert": (alert_created_count / detail_view_count * 100) if detail_view_count > 0 else 0
        }
        
        # Top searches
        top_searches = db.query(
            query_expr.label("query"),
            func.count(AnalyticsEvent.id).label('count')
        ).filter(
            AnalyticsEvent.event_name == "search_triggered",
            AnalyticsEvent.created_at >= since
        ).group_by(
            query_expr
        ).order_by(
            desc(func.count(AnalyticsEvent.id))
        ).limit(5).all()

        # Retention Metrics (M2-02, M2-03, M2-04, M2-05)
        alert_return_click = stats.get("alert_return_click", 0)
        insight_page_view = stats.get("insight_page_view", 0)
        insight_event_click = stats.get("insight_event_click", 0)
        product_follow_count = stats.get("product_follow", 0)
        
        retention_metrics = {
            "alert_return_rate": (alert_return_click / alert_created_count * 100) if alert_created_count > 0 else 0,
            "insight_click_rate": (insight_event_click / insight_page_view * 100) if insight_page_view > 0 else 0,
            "total_new_follows": product_follow_count,
            "follow_list_clicks": stats.get("follow_list_detail_click", 0)
        }

        return {
            "raw_counts": stats,
            "funnel": funnel,
            "retention_metrics": retention_metrics,
            "top_searches": [{"query": r[0] if r[0] else 'N/A', "count": r[1]} for r in top_searches],
            "period_days": days
        }
