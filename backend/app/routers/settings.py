"""
Purpose: Global settings endpoints — logo URL, signature URL.
Owner: [Claude]
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.global_setting import GlobalSetting
from app.models.user import User
from app.schemas.global_setting import SettingRead, SettingUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=list[SettingRead])
def get_all_settings(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Return all global settings (logo URL, signature URL).
    Inputs: none
    Outputs: list[SettingRead]
    Owner: [Claude]
    """
    return db.query(GlobalSetting).order_by(GlobalSetting.key).all()


@router.put("/{key}", response_model=SettingRead)
def update_setting(
    key: str,
    body: SettingUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Update a global setting value by key.
    Inputs: key (str path param), SettingUpdate (value: any JSON)
    Outputs: SettingRead
    Owner: [Claude]
    """
    setting = db.query(GlobalSetting).filter(GlobalSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found.")
    setting.value = body.value
    db.commit()
    db.refresh(setting)
    return setting
