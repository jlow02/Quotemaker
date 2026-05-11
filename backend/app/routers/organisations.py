"""
Purpose: Organisation CRUD + autocomplete endpoints. Shared client database entity.
         Soft delete only — hard delete blocked to protect CostingSheet history.
Owner: [Claude]
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.organisation import Organisation
from app.models.user import User
from app.schemas.organisation import (
    OrganisationCreate, OrganisationRead, OrganisationUpdate, OrganisationAutocomplete
)

router = APIRouter(prefix="/organisations", tags=["Organisations"])


@router.get("", response_model=list[OrganisationRead])
def list_organisations(
    q: Optional[str] = Query(None, description="Name search filter"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: List all active (non-deleted) organisations; supports optional name search.
    Inputs: q (Optional[str]) — name substring filter
    Outputs: list[OrganisationRead]
    Owner: [Claude]
    """
    query = db.query(Organisation).filter(Organisation.deleted_at.is_(None))
    if q:
        query = query.filter(Organisation.name.ilike(f"%{q}%"))
    return query.order_by(Organisation.name).all()


@router.get("/autocomplete", response_model=list[OrganisationAutocomplete])
def autocomplete_organisations(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Typeahead autocomplete — returns id+name only for lightweight dropdown.
    Inputs: q (str) — search prefix
    Outputs: list[OrganisationAutocomplete]
    Owner: [Claude]
    """
    return (
        db.query(Organisation)
        .filter(Organisation.deleted_at.is_(None), Organisation.name.ilike(f"%{q}%"))
        .order_by(Organisation.name)
        .limit(10)
        .all()
    )


@router.post("", response_model=OrganisationRead, status_code=status.HTTP_201_CREATED)
def create_organisation(
    body: OrganisationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Create a new organisation in the shared client database.
    Inputs: OrganisationCreate (name, address)
    Outputs: OrganisationRead
    Owner: [Claude]
    """
    org = Organisation(
        name=body.name,
        address=body.address,
        created_by_user_id=current_user.id,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.get("/{org_id}", response_model=OrganisationRead)
def get_organisation(
    org_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Retrieve a single organisation by ID (active only).
    Inputs: org_id (str UUID path param)
    Outputs: OrganisationRead
    Owner: [Claude]
    """
    org = db.query(Organisation).filter(
        Organisation.id == org_id,
        Organisation.deleted_at.is_(None),
    ).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found.")
    return org


@router.put("/{org_id}", response_model=OrganisationRead)
def update_organisation(
    org_id: str,
    body: OrganisationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Update name or address of an organisation.
    Inputs: org_id (str UUID), OrganisationUpdate (name, address — both optional)
    Outputs: OrganisationRead
    Owner: [Claude]
    """
    org = db.query(Organisation).filter(
        Organisation.id == org_id,
        Organisation.deleted_at.is_(None),
    ).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found.")
    if body.name is not None:
        org.name = body.name
    if body.address is not None:
        org.address = body.address
    db.commit()
    db.refresh(org)
    return org


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organisation(
    org_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Soft-delete an organisation (set deleted_at). FK on CostingSheet remains intact.
             Hard delete is blocked to protect CostingSheet relational history.
    Inputs: org_id (str UUID)
    Outputs: 204 No Content
    Owner: [Claude]
    """
    org = db.query(Organisation).filter(
        Organisation.id == org_id,
        Organisation.deleted_at.is_(None),
    ).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found.")
    org.deleted_at = datetime.now(timezone.utc)
    db.commit()
