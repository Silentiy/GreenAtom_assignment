from datetime import datetime
from pydantic import BaseModel


class InboxBase(BaseModel):
    """Schema for fastAPI responses
    Contains fields suitable both for POST and GET"""

    stored_file_name: str
    registration_date_time: datetime


class InboxCreate(InboxBase):
    """ Schema for fastAPI responses with additional fields for POST """
    request_code: str


class Inbox(InboxBase):
    """ Schema for fastAPI responses with additional fields for GET """
    pass

    class Config:
        orm_mode = True
