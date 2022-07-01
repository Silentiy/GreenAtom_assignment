import os
from fastapi import FastAPI, UploadFile, Request, Depends, Query, HTTPException
from minio.deleteobjects import DeleteObject
import uuid
from typing import List
from minio import Minio
from minio.error import S3Error
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from collections import defaultdict

from sql_part import crud, models, schemas
from sql_part.database import SessionLocal, engine


def logger():
    """Return logger with defined parameters"""
    now = datetime.now()
    log_name = now.strftime("%Y%m%d%H%M%S") + '.log'
    path_to_log = "./logs"
    os.makedirs(path_to_log, exist_ok=True)
    log_file_name = path_to_log + "/" + log_name
    logging.basicConfig(filename=log_file_name, encoding='utf-8', level=logging.DEBUG)
    return logging.getLogger()


models.Base.metadata.create_all(bind=engine)
app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def read_main():
    return {"msg": "Hello World"}


def create_minio_client():
    """Return MinIO client with specified parameters"""

    client = Minio(
        "127.0.0.1:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    logger().debug("Minio client has been created")

    return client


def get_minio_bucket():
    """Checks whether bucket name with name <YYYYMMDD> exists and
    creates a bucket if it does not exist"""

    client = create_minio_client()

    now = datetime.now()
    bucket_name = now.strftime("%Y%m%d")

    # Make 'YYYYMMDD' bucket if not exist
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)
        logger().debug(f"Bucket '{bucket_name}' successfully created")
    else:
        logger().debug(f"Bucket '{bucket_name}' already exists")

    return bucket_name


def store_object(file_name):
    """Stores object with name <uuid>.jpg to the MinIO object storage
     in a bucket with name <YYYYMMDD>"""

    client = create_minio_client()
    bucket_name = get_minio_bucket()

    object_name = str(uuid.uuid4()) + ".jpg"

    client.fput_object(
        bucket_name=bucket_name, object_name=object_name, file_path=file_name)
    logger().debug(
        f"'{file_name}' is successfully uploaded as "
        f"object '{object_name}' to bucket '{bucket_name}'."
    )

    return object_name


def validate_incoming_files(files: List[UploadFile]):
    """ Makes validation of lengths of incoming list of files """
    if len(files) > 15 or len(files) <= 0:
        raise HTTPException(
            status_code=400,
            detail="You can only upload from 1 to 15 images"
        )
    return True


@app.post(path="/frames/")
def upload_and_register_files(files: List[UploadFile], request: Request, db: Session = Depends(get_db)):
    """ Uploads received files to the object storage
     and registers date and time of saving, request url and files names as well as
     files names in bucket into sqlite DB """

    if validate_incoming_files(files) is True:
        now = datetime.now()

        # collect info about request
        post_request = [request.url,
                        {"names_of_posted_files": [file.filename for file in files]}]
        post_request_strings_list = list()
        for value in post_request:
            post_request_strings_list.append(str(value))
        post_request_string = " ".join(post_request_strings_list)
        logger().debug(post_request_string)

        # store files in object storage and register info in DB
        filenames = list()
        for file in files:
            try:
                filename = store_object(file.file.fileno())
            except S3Error as exc:
                logging.debug("Error occurred while downloading a file to the object storage", exc)
                continue
            filenames.append(filename)
            message = schemas.InboxCreate(request_code=post_request_string,
                                          stored_file_name=filename,
                                          registration_date_time=now)
            crud.create_inbox_message(db=db, message=message)

        return {"filenames_in_object_storage": [filename for filename in filenames]}


@app.get(path="/frames/get/", response_model=list[schemas.Inbox])
def get_data_by_date(date_lower: str,
                     date_upper: str,
                     limit: int,
                     db: Session = Depends(get_db)):
    """ Returns json with names of files in a bucket
    satisfying the requested time period """

    date_lower = datetime.strptime(date_lower, "%Y-%m-%d_%H:%M:%S")
    date_upper = datetime.strptime(date_upper, "%Y-%m-%d_%H:%M:%S")

    data = crud.get_files_by_date(date_lower_limit=date_lower,
                                  date_upper_limit=date_upper,
                                  number_of_files=limit,
                                  db=db)
    if len(data) == 0:
        raise HTTPException(
            status_code=404,
            detail="No files satisfying given dates"
        )
    return data


@app.delete(path="/frames/delete/", status_code=204)
def delete_files_and_data_by_uuids(files_names: list[str] = Query(...), db: Session = Depends(get_db)):
    """ Deletes files with specified uuids from the object storage
    and cleans info from database """

    minio_client = create_minio_client()
    file_not_found = list()
    files_to_delete = defaultdict(list)
    affected_rows = 0
    data = None

    # get existing files
    for file_name in files_names:
        data = crud.get_file_by_uuid(file_uuid=file_name, db=db)
        if data:
            key = datetime.strftime(data.registration_date_time, "%Y%m%d")  # bucket
            files_to_delete[key].append(data.stored_file_name)
        else:
            file_not_found.append(file_name)

    # delete existing files from object storage and, if successful, from db
    for key in files_to_delete.keys():
        list_to_delete = list()
        for file_name in files_to_delete[key]:
            list_to_delete.append(DeleteObject(file_name))
        logger().info(list_to_delete)
        errors = minio_client.remove_objects(
            bucket_name=str(key),
            delete_object_list=list_to_delete
        )
        logging.info(errors)
        for error in errors:
            logger().debug("Error occurred when deleting object", error)
        if len(list(errors)) == 0:
            logger().info("No errors during deletion objects from object storage")
            affected_rows = crud.delete_data_by_uuids(files_uuids=files_names, db=db)

    if not data:
        raise HTTPException(
            status_code=404,
            detail="No files satisfying given dates"
        )

