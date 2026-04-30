from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import Product as ProductSchema, ProductCreate, PriceHistoryStats, ProductDetailResponse, ProductFollow
from app.services.product_service import ProductService
from app.api.v1.deps import PermissionChecker, get_current_user


from app.utils.responses import response_success

router = APIRouter(prefix="/products", tags=["products"])
product_service = ProductService()


@router.get("")
def list_products(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all products with their SKUs."""
    products = product_service.list_products(db, skip=skip, limit=limit)
    # Validate each product with the schema to ensure proper serialization of nested models
    data = [ProductSchema.model_validate(p) for p in products]
    return response_success(data)


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(PermissionChecker(["AC_100010"]))])
def create_product(
    *,
    db: Session = Depends(get_db),
    product_in: ProductCreate,
) -> Any:
    """Create a new product."""
    product = product_service.create_product(db, product_in.model_dump())
    return response_success(product)


@router.get("/follows")
def list_followed_products(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """List products followed by the current user."""
    follows = product_service.list_followed_products(db, current_user["id"])
    data = [ProductFollow.model_validate(f) for f in follows]
    return response_success(data)


@router.get("/{product_id}")
def get_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Get a specific product by ID, including user-specific follow status and alerts."""
    detail = product_service.get_product_detail(db, product_id, current_user["id"])
    if not detail["product"]:
        raise HTTPException(status_code=404, detail="Product not found")
    return response_success(ProductDetailResponse.model_validate(detail))


@router.post("/{product_id}/follow")
def follow_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Follow a product."""
    follow = product_service.follow_product(db, current_user["id"], product_id)
    return response_success(ProductFollow.model_validate(follow))


@router.delete("/{product_id}/follow")
def unfollow_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Unfollow a product."""
    success = product_service.unfollow_product(db, current_user["id"], product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Follow relationship not found")
    return response_success(None, "Unfollowed successfully")


@router.delete("/{product_id}", dependencies=[Depends(PermissionChecker(["AC_100010"]))])
def delete_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
) -> Any:
    """Delete a product."""
    success = product_service.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return response_success(None, "Product deleted successfully")


@router.get("/skus/{sku_id}/history")
def get_sku_price_history(
    *,
    db: Session = Depends(get_db),
    sku_id: int,
    days: int = Query(30, ge=1, le=180),
) -> Any:
    """Get price history and stats for a specific SKU."""
    history = product_service.get_price_history(db, sku_id, days)
    return response_success(history)


@router.get("/{product_id}/alternatives")
def get_product_alternatives(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    limit: int = Query(5, ge=1, le=20),
) -> Any:
    """Get alternative products in the same category."""
    products = product_service.get_alternatives(db, product_id, limit=limit)
    data = [ProductSchema.model_validate(p) for p in products]
    return response_success(data)
