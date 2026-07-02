"""
Chat / Messaging Routes
Candidates and recruiters can exchange messages on an application.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.database import get_db
from app.auth.utils import get_current_user
from app.models.user import User
from app.models.recruiter import Application, RecruiterJobPost
from app.models.message import Message
from typing import List


router = APIRouter(prefix="/chat", tags=["chat"])


class MessageSend(BaseModel):
    application_id: int
    content: str


class MessageResponse(BaseModel):
    id: int
    application_id: int
    sender_id: int
    sender_name: str
    sender_role: str
    content: str
    is_read: bool
    created_at: str


def _verify_participant(app_id: int, user: User, db: Session):
    """Verify user is either the candidate or recruiter for this application."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    is_candidate = app.user_id == user.id
    is_recruiter = False
    if not is_candidate:
        jp = db.query(RecruiterJobPost).filter(
            RecruiterJobPost.id == app.job_post_id,
            RecruiterJobPost.recruiter_id == user.id,
        ).first()
        is_recruiter = jp is not None

    if not is_candidate and not is_recruiter:
        raise HTTPException(status_code=403, detail="Access denied")
    return app


@router.post("/messages")
def send_message(
    body: MessageSend,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message on an application."""
    app = _verify_participant(body.application_id, current_user, db)

    msg = Message(
        application_id=body.application_id,
        sender_id=current_user.id,
        content=body.content.strip(),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {
        "id": msg.id,
        "application_id": msg.application_id,
        "sender_id": msg.sender_id,
        "sender_name": current_user.name,
        "sender_role": "recruiter" if current_user.is_recruiter else "candidate",
        "content": msg.content,
        "is_read": msg.is_read,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


@router.get("/applications/{application_id}/messages")
def get_messages(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all messages for an application."""
    _verify_participant(application_id, current_user, db)

    messages = db.query(Message).filter(
        Message.application_id == application_id
    ).order_by(Message.created_at).all()

    # Mark unread messages as read (messages sent by the other party)
    updated = False
    for m in messages:
        if not m.is_read and m.sender_id != current_user.id:
            m.is_read = True
            updated = True
    if updated:
        db.commit()

    result = []
    for m in messages:
        sender = db.query(User).filter(User.id == m.sender_id).first()
        result.append({
            "id": m.id,
            "application_id": m.application_id,
            "sender_id": m.sender_id,
            "sender_name": sender.name if sender else "Unknown",
            "sender_role": "recruiter" if (sender and sender.is_recruiter) else "candidate",
            "content": m.content,
            "is_read": m.is_read,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })
    return result


@router.get("/applications/{application_id}/unread-count")
def get_unread_count(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get count of unread messages from the other party."""
    _verify_participant(application_id, current_user, db)

    count = db.query(Message).filter(
        Message.application_id == application_id,
        Message.sender_id != current_user.id,
        Message.is_read == False,
    ).count()

    return {"unread_count": count}
