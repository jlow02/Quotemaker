"""
Purpose: Product CRUD endpoints. Products are a reference catalogue; soft-deleted only.
Owner: [Claude]
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductRead])
def list_products(
    category: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: List active products with optional category and name filters.
    Inputs: category (Optional[str]), name (Optional[str])
    Outputs: list[ProductRead]
    Owner: [Claude]
    """
    q = db.query(Product).filter(Product.deleted_at.is_(None))
    if category:
        q = q.filter(Product.category == category)
    if name:
        q = q.filter(Product.name.ilike(f"%{name}%"))
    return q.order_by(Product.category, Product.name).all()


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Create a new product in the catalogue.
    Inputs: ProductCreate
    Outputs: ProductRead
    Owner: [Claude]
    """
    product = Product(**body.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Get a single product by ID (active only).
    Inputs: product_id (str UUID)
    Outputs: ProductRead
    Owner: [Claude]
    """
    product = db.query(Product).filter(
        Product.id == product_id, Product.deleted_at.is_(None)
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: str,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Update a product's fields.
    Inputs: product_id (str UUID), ProductUpdate
    Outputs: ProductRead
    Owner: [Claude]
    """
    product = db.query(Product).filter(
        Product.id == product_id, Product.deleted_at.is_(None)
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Soft-delete a product. Existing line items using it are unaffected (fields copied on add).
    Inputs: product_id (str UUID)
    Outputs: 204 No Content
    Owner: [Claude]
    """
    product = db.query(Product).filter(
        Product.id == product_id, Product.deleted_at.is_(None)
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    product.deleted_at = datetime.now(timezone.utc)
    db.commit()
