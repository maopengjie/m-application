import os
import sys
from sqlalchemy import create_url
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

# Add app to path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.models.analytics import AnalyticsEvent

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

with Session(engine) as session:
    try:
        # Test basic JSON access
        query = session.query(
            AnalyticsEvent.properties["q"]
        ).filter(AnalyticsEvent.event_name == "search_triggered").limit(1)
        print("Basic access:", query.all())
    except Exception as e:
        print("Basic access failed:", e)

    try:
        # Test as_string or similar
        query = session.query(
            AnalyticsEvent.properties["q"].as_string()
        ).filter(AnalyticsEvent.event_name == "search_triggered").limit(1)
        print("as_string access:", query.all())
    except Exception as e:
        print("as_string access failed:", e)

    try:
        # Test JSON_UNQUOTE
        query = session.query(
            func.json_unquote(func.json_extract(AnalyticsEvent.properties, "$.q"))
        ).filter(AnalyticsEvent.event_name == "search_triggered").limit(1)
        print("JSON_UNQUOTE access:", query.all())
    except Exception as e:
        print("JSON_UNQUOTE access failed:", e)
