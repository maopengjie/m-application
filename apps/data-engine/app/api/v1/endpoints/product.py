from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import Product as ProductSchema, ProductCreate, PriceHistoryStats
from app.services.product_service import ProductService
from app.api.v1.deps import PermissionChecker

router = APIRouter(prefix="/products", tags=["products"])
product_service = ProductService()


@router.get("", response_model=List[ProductSchema])
def list_products(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all products with their SKUs."""
    return product_service.list_products(db, skip=skip, limit=limit)


@router.post("", response_model=ProductSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(PermissionChecker(["AC_100010"]))])
def create_product(
    *,
    db: Session = Depends(get_db),
    product_in: ProductCreate,
) -> Any:
    """Create a new product."""
    return product_service.create_product(db, product_in.model_dump())


@router.get("/{product_id}", response_model=ProductSchema)
def get_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
) -> Any:
    """Get a specific product by ID, including full details (SKUs, history, etc.)."""
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


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
    return {"message": "Product deleted successfully"}


@router.get("/skus/{sku_id}/history", response_model=PriceHistoryStats)
def get_sku_price_history(
    *,
    db: Session = Depends(get_db),
    sku_id: int,
    days: int = Query(30, ge=1, le=180),
) -> Any:
    """Get price history and stats for a specific SKU."""
    return product_service.get_price_history(db, sku_id, days)
