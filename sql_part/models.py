from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime

from . database import Base


class Inbox(Base):
    """ Data model description """

    __tablename__ = "inbox"

    id = Column(Integer, primary_key=True, index=True)
    request_code = Column(String)
    stored_file_name = Column(String, unique=True, index=True)
    registration_date_time = Column(DateTime, index=True)
