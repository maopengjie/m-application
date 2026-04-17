from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import Product as ProductSchema, ProductCreate, PriceHistoryStats
from app.services.product_service import ProductService
from app.api.v1.deps import PermissionChecker

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


@router.get("/{product_id}")
def get_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
) -> Any:
    """Get a specific product by ID, including full details (SKUs, history, etc.)."""
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Validate with the schema to ensure proper serialization of nested models (skus, coupons, etc.)
    return response_success(ProductSchema.model_validate(product))


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
