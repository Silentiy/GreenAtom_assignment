from sqlalchemy.orm import Session
from typing import Union
import datetime
from typing import List
import logging
from datetime import datetime

from . import models, schemas


# create
def create_inbox_message(db: Session, message: schemas.InboxCreate):
    db_message = models.Inbox(request_code=message.request_code,
                              stored_file_name=message.stored_file_name,
                              registration_date_time=message.registration_date_time)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


# read
def get_files_by_uuids(db: Session, files_uuids: list[str]):
    return db.query(models.Inbox).filter(models.Inbox.stored_file_name.in_(files_uuids)).all()


def get_file_by_uuid(db: Session, file_uuid: str):
    return db.query(models.Inbox).filter(models.Inbox.stored_file_name == file_uuid).first()


def get_data_by_id(db: Session, line_id: int):
    return db.query(models.Inbox).filter(models.Inbox.id == line_id).first()


def get_files_by_date(db: Session,
                      date_lower_limit: datetime,
                      date_upper_limit: datetime,
                      number_of_files: int = 5):
    return db.query(models.Inbox).filter(
        models.Inbox.registration_date_time >= date_lower_limit,
        models.Inbox.registration_date_time <= date_upper_limit).limit(number_of_files).all()


def delete_data_by_uuids(db: Session, files_uuids: list[str]):
    results = db.query(models.Inbox).filter(models.Inbox.stored_file_name.in_(files_uuids)).delete()
    db.commit()
    return results


def delete_data_by_uuid(db: Session, file_uuid: str):
    data_to_delete = db.query(models.Inbox).filter(models.Inbox.stored_file_name == file_uuid).first()
    # results = db.delete(data_to_delete)
    # db.commit()
    return data_to_delete


def delete_data_by_id(db: Session, line_id: int):

    now = datetime.now()
    log_name = now.strftime("%Y%m%d%H%M%S") + '.log'
    logging.basicConfig(filename=log_name, encoding='utf-8', level=logging.DEBUG)
    logging.debug(f"line_id is {line_id}")

    results = db.query(models.Inbox).filter(models.Inbox.id == line_id).delete()
    db.commit()
    return results
