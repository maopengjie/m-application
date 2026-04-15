from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import Product as ProductSchema, ProductCreate
from app.services.product_service import ProductService

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


@router.post("", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
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


@router.delete("/{product_id}")
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
