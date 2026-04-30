from fastapi import APIRouter

from app.api.v1.endpoints import (
    alert,
    analysis,
    auth,
    crawler,
    decision,
    price,
    product,
    search,
    system,
    users,
    menu,
    coupon,
    risk,
    analytics,
    insight,
    intelligence,
)

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(menu.router)
api_router.include_router(users.router)
api_router.include_router(crawler.router)
api_router.include_router(analysis.router)
api_router.include_router(price.router)
api_router.include_router(product.router)
api_router.include_router(search.router)
api_router.include_router(decision.router)
api_router.include_router(alert.router)
api_router.include_router(coupon.router)
api_router.include_router(risk.router)
api_router.include_router(analytics.router)
api_router.include_router(insight.router)
api_router.include_router(intelligence.router)
