import base64
import mimetypes
from email.message import EmailMessage
import os
from email.message import EmailMessage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

from auth.gmail_auth import get_gmail_service
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pathlib import Path


def gmail_create_draft_with_attachment(attachment_filename: str):

    try:
        service = get_gmail_service()
        mime_message = EmailMessage()

        # headers
        mime_message["To"] = "jasonhjx1207@gmail.com"
        mime_message["From"] = "hjasonjx@gmail.com"
        mime_message["Subject"] = "TLDR Podcast Episode"

        # text
        mime_message.set_content(
            "Hi, this is your daily episode of the TLDR Podcast."
        )

        # attachment
        attachment_part = build_file_part(attachment_filename)

        mime_message.make_mixed()
        mime_message.attach(attachment_part)

        encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
        create_draft_request_body = {"message": {"raw": encoded_message}}
        
        # draft
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body=create_draft_request_body)
            .execute()
        )

        # sending
        sent = (
            service.users()
            .drafts()
            .send(userId="me", body={"id": draft["id"]})
            .execute()
        )
        print(f'Sent message id: {sent["id"]}\nDraft id: {draft["id"]}\nDraft message: {draft["message"]}')
    except HttpError as error:
        print(f'An error occurred: {error}')
        draft = None
    return draft

def build_file_part(file):
    file_path = Path(__file__).resolve().parent / file
    content_type, encoding = mimetypes.guess_type(file_path)
    if content_type is None or encoding is not None:
        content_type = "application/octet-stream"
    main_type, sub_type = content_type.split("/", 1)

    with open(file_path, "rb") as f:
        file_data = f.read()

    if main_type == "text":
        msg = MIMEText(file_data.decode("utf-8"), _subtype=sub_type)
    elif main_type == "image":
        msg = MIMEImage(file_data, _subtype=sub_type)
    elif main_type == "audio":
        msg = MIMEAudio(file_data, _subtype=sub_type)
    else:
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(file_data)

    filename = os.path.basename(file_path)
    msg.add_header("Content-Disposition", "attachment", filename=filename)
    return msg

def gmail_send_message():
  """Create and send an email message
  Print the returned  message id
  Returns: Message object, including message id

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """

  try:
    service = get_gmail_service()
    message = EmailMessage()

    message.set_content("This is automated draft mail")

    message["To"] = "jasonhjx1207@gmail.com"
    message["From"] = "hjasonjx@gmail.com"
    message["Subject"] = "Test TLDR Podcast Episode"

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    # pylint: disable=E1101
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f'Message Id: {send_message["id"]}')
  except HttpError as error:
    print(f"An error occurred: {error}")
    send_message = None
  return send_message

if __name__=='__main__':
    gmail_create_draft_with_attachment('test_file.txt')