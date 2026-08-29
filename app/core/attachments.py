from io import BytesIO
import csv

import pandas as pd
from pypdf import PdfReader

from .gmail import decode_body


# ============================================================
# DOWNLOAD ATTACHMENT
# ============================================================

def get_attachment_data(
    service,
    message_id,
    attachment_id
):
    attachment = (
        service.users()
        .messages()
        .attachments()
        .get(
            userId="me",
            messageId=message_id,
            id=attachment_id
        )
        .execute()
    )

    data = attachment.get("data")

    if not data:
        return None

    return decode_body(data)


# ============================================================
# TEXT MATCH
# ============================================================

def text_matches(text, query):

    if text is None:
        return False

    return query.lower() in str(text).lower()


# ============================================================
# SEARCH EXCEL
# ============================================================

def search_excel_attachment(
    service,
    message_id,
    part,
    query
):

    filename = part.get(
        "filename",
        ""
    )

    if not filename.lower().endswith(
        (".xlsx", ".xls")
    ):
        return []

    attachment_id = (
        part
        .get("body", {})
        .get("attachmentId")
    )

    if not attachment_id:
        return []

    data = get_attachment_data(
        service,
        message_id,
        attachment_id
    )

    if not data:
        return []

    results = []

    try:

        sheets = pd.read_excel(
            BytesIO(data),
            sheet_name=None,
            header=None
        )

        for sheet_name, df in sheets.items():

            for row_index, row in df.iterrows():

                for column_index, value in row.items():

                    if text_matches(
                        value,
                        query
                    ):

                        excel_row = row_index + 1
                        excel_column = column_index + 1

                        # Convert column number to Excel letters
                        letters = ""
                        number = excel_column

                        while number:

                            number, remainder = divmod(
                                number - 1,
                                26
                            )

                            letters = (
                                chr(
                                    65 + remainder
                                )
                                + letters
                            )

                        results.append({

                            "filename": filename,

                            "type": "excel",

                            "sheet": str(
                                sheet_name
                            ),

                            "cell": (
                                f"{letters}"
                                f"{excel_row}"
                            ),

                            "match": str(
                                value
                            )

                        })

    except Exception:

        return []

    return results


# ============================================================
# SEARCH CSV
# ============================================================

def search_csv_attachment(
    service,
    message_id,
    part,
    query
):

    filename = part.get(
        "filename",
        ""
    )

    if not filename.lower().endswith(
        ".csv"
    ):
        return []

    attachment_id = (
        part
        .get("body", {})
        .get("attachmentId")
    )

    if not attachment_id:
        return []

    data = get_attachment_data(
        service,
        message_id,
        attachment_id
    )

    if not data:
        return []

    results = []

    try:

        text = data.decode(
            "utf-8",
            errors="replace"
        )

        reader = csv.reader(
            text.splitlines()
        )

        for row_number, row in enumerate(
            reader,
            start=1
        ):

            for column_number, value in enumerate(
                row,
                start=1
            ):

                if text_matches(
                    value,
                    query
                ):

                    results.append({

                        "filename": filename,

                        "type": "csv",

                        "row": row_number,

                        "column": column_number,

                        "match": value

                    })

    except Exception:

        return []

    return results


# ============================================================
# SEARCH TEXT FILE
# ============================================================

def search_txt_attachment(
    service,
    message_id,
    part,
    query
):

    filename = part.get(
        "filename",
        ""
    )

    if not filename.lower().endswith(
        (
            ".txt",
            ".log",
            ".md"
        )
    ):
        return []

    attachment_id = (
        part
        .get("body", {})
        .get("attachmentId")
    )

    if not attachment_id:
        return []

    data = get_attachment_data(
        service,
        message_id,
        attachment_id
    )

    if not data:
        return []

    results = []

    try:

        text = data.decode(
            "utf-8",
            errors="replace"
        )

        lines = text.splitlines()

        for line_number, line in enumerate(
            lines,
            start=1
        ):

            if text_matches(
                line,
                query
            ):

                results.append({

                    "filename": filename,

                    "type": "text",

                    "line": line_number,

                    "match": line

                })

    except Exception:

        return []

    return results


# ============================================================
# SEARCH PDF
# ============================================================

def search_pdf_attachment(
    service,
    message_id,
    part,
    query
):

    filename = part.get(
        "filename",
        ""
    )

    if not filename.lower().endswith(
        ".pdf"
    ):
        return []

    attachment_id = (
        part
        .get("body", {})
        .get("attachmentId")
    )

    if not attachment_id:
        return []

    data = get_attachment_data(
        service,
        message_id,
        attachment_id
    )

    if not data:
        return []

    results = []

    try:

        reader = PdfReader(
            BytesIO(data)
        )

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            text = page.extract_text()

            if text_matches(
                text,
                query
            ):

                results.append({

                    "filename": filename,

                    "type": "pdf",

                    "page": page_number,

                    "match": query

                })

    except Exception:

        return []

    return results


# ============================================================
# SEARCH ALL ATTACHMENTS
# ============================================================

def search_attachments(
    service,
    message_id,
    payload,
    query
):

    results = []

    for part in payload.get(
        "parts",
        []
    ):

        # ----------------------------------------------------
        # Excel
        # ----------------------------------------------------

        results.extend(
            search_excel_attachment(
                service,
                message_id,
                part,
                query
            )
        )

        # ----------------------------------------------------
        # CSV
        # ----------------------------------------------------

        results.extend(
            search_csv_attachment(
                service,
                message_id,
                part,
                query
            )
        )

        # ----------------------------------------------------
        # PDF
        # ----------------------------------------------------

        results.extend(
            search_pdf_attachment(
                service,
                message_id,
                part,
                query
            )
        )

        # ----------------------------------------------------
        # TXT / LOG / MD
        # ----------------------------------------------------

        results.extend(
            search_txt_attachment(
                service,
                message_id,
                part,
                query
            )
        )

        # ----------------------------------------------------
        # Nested MIME parts
        # ----------------------------------------------------

        if part.get("parts"):

            results.extend(
                search_attachments(
                    service,
                    message_id,
                    part,
                    query
                )
            )

    return results