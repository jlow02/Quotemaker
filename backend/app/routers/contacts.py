"""
Purpose: Contact CRUD + autocomplete endpoints. Scoped to an Organisation.
         Soft delete only — hard delete blocked to protect CostingSheet history.
Owner: [Claude]
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.contact import Contact
from app.models.organisation import Organisation
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate, ContactAutocomplete

router = APIRouter(tags=["Contacts"])


def _get_active_org(org_id: str, db: Session) -> Organisation:
    """
    Purpose: Fetch an active (non-deleted) organisation or raise 404.
    Inputs: org_id (str), db (Session)
    Outputs: Organisation
    Owner: [Claude]
    """
    org = db.query(Organisation).filter(
        Organisation.id == org_id,
        Organisation.deleted_at.is_(None),
    ).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found.")
    return org


@router.get("/organisations/{org_id}/contacts", response_model=list[ContactRead])
def list_contacts(
    org_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: List all active contacts for an organisation.
    Inputs: org_id (str UUID path param)
    Outputs: list[ContactRead]
    Owner: [Claude]
    """
    _get_active_org(org_id, db)
    return (
        db.query(Contact)
        .filter(Contact.organisation_id == org_id, Contact.deleted_at.is_(None))
        .order_by(Contact.name)
        .all()
    )


@router.get("/organisations/{org_id}/contacts/autocomplete", response_model=list[ContactAutocomplete])
def autocomplete_contacts(
    org_id: str,
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Typeahead autocomplete for contacts within an organisation.
    Inputs: org_id (str UUID), q (str) — name search prefix
    Outputs: list[ContactAutocomplete]
    Owner: [Claude]
    """
    _get_active_org(org_id, db)
    return (
        db.query(Contact)
        .filter(
            Contact.organisation_id == org_id,
            Contact.deleted_at.is_(None),
            Contact.name.ilike(f"%{q}%"),
        )
        .order_by(Contact.name)
        .limit(10)
        .all()
    )


@router.post("/organisations/{org_id}/contacts", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(
    org_id: str,
    body: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purpose: Create a new contact within an organisation.
    Inputs: org_id (str UUID), ContactCreate (name, email, phone)
    Outputs: ContactRead
    Owner: [Claude]
    """
    _get_active_org(org_id, db)
    contact = Contact(
        organisation_id=org_id,
        name=body.name,
        email=body.email,
        phone=body.phone,
        created_by_user_id=current_user.id,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/contacts/{contact_id}", response_model=ContactRead)
def get_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Get a single contact by ID (active only).
    Inputs: contact_id (str UUID)
    Outputs: ContactRead
    Owner: [Claude]
    """
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.deleted_at.is_(None),
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")
    return contact


@router.put("/contacts/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: str,
    body: ContactUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Update a contact's name, email, or phone.
    Inputs: contact_id (str UUID), ContactUpdate
    Outputs: ContactRead
    Owner: [Claude]
    """
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.deleted_at.is_(None),
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")
    if body.name is not None:
        contact.name = body.name
    if body.email is not None:
        contact.email = body.email
    if body.phone is not None:
        contact.phone = body.phone
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Soft-delete a contact (set deleted_at). FK on CostingSheet remains intact.
    Inputs: contact_id (str UUID)
    Outputs: 204 No Content
    Owner: [Claude]
    """
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.deleted_at.is_(None),
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")
    contact.deleted_at = datetime.now(timezone.utc)
    db.commit()
