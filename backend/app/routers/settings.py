"""
Purpose: Global settings endpoints — system-wide key-value configuration store.
Owner: [Claude]
"""
from fastapi import APIRouter, Depends
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
    Purpose: Return all global settings.
    Inputs: none
    Outputs: list[SettingRead]
    Owner: [Claude]
    """
    return db.query(GlobalSetting).order_by(GlobalSetting.key).all()


@router.put("/{key}", response_model=SettingRead)
def upsert_setting(
    key: str,
    body: SettingUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Purpose: Create-or-update (upsert) a global setting by key.
             If the key does not exist it is created; otherwise its value is updated.
    Inputs: key (str path param), SettingUpdate (value: any JSON)
    Outputs: SettingRead
    Owner: [Claude]
    """
    setting = db.query(GlobalSetting).filter(GlobalSetting.key == key).first()
    if not setting:
        setting = GlobalSetting(key=key, value=body.value)
        db.add(setting)
    else:
    