from typing import Optional


def build_gmail_query(
    query: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    sender: Optional[str] = None,
    recipient: Optional[str] = None,
    subject: Optional[str] = None,
    has_attachment: Optional[bool] = None,
    is_unread: Optional[bool] = None,
    is_starred: Optional[bool] = None,
    label: Optional[str] = None,
    folder: Optional[str] = None,
    larger_than: Optional[int] = None,
    smaller_than: Optional[int] = None,
    raw_query: Optional[str] = None,
):
    """
    Convert API filters into a Gmail search query.

    Dates:
        from_date = YYYY-MM-DD
        to_date   = YYYY-MM-DD

    Note:
        Gmail's before: operator is exclusive.
        Therefore, to include the entire to_date,
        we add one day internally.
    """

    filters = []

    # ---------------------------------------------------------
    # Free-text search
    # ---------------------------------------------------------

    if query:
        filters.append(query.strip())

    # ---------------------------------------------------------
    # Date filters
    # ---------------------------------------------------------

    if from_date:
        filters.append(
            f"after:{from_date.replace('-', '/')}"
        )

    if to_date:
        # Gmail before: is exclusive.
        # Example:
        # to_date = 2026-08-30
        # becomes before:2026/08/31
        from datetime import datetime, timedelta

        date_obj = datetime.strptime(
            to_date,
            "%Y-%m-%d"
        )

        next_day = date_obj + timedelta(days=1)

        filters.append(
            f"before:{next_day.strftime('%Y/%m/%d')}"
        )

    # ---------------------------------------------------------
    # Sender / recipient
    # ---------------------------------------------------------

    if sender:
        filters.append(
            f"from:{sender}"
        )

    if recipient:
        filters.append(
            f"to:{recipient}"
        )

    # ---------------------------------------------------------
    # Subject
    # ---------------------------------------------------------

    if subject:
        filters.append(
            f"subject:{subject}"
        )

    # ---------------------------------------------------------
    # Attachment
    # ---------------------------------------------------------

    if has_attachment is True:
        filters.append("has:attachment")

    elif has_attachment is False:
        filters.append("-has:attachment")

    # ---------------------------------------------------------
    # Read / unread
    # ---------------------------------------------------------

    if is_unread is True:
        filters.append("is:unread")

    elif is_unread is False:
        filters.append("is:read")

    # ---------------------------------------------------------
    # Starred
    # ---------------------------------------------------------

    if is_starred is True:
        filters.append("is:starred")

    elif is_starred is False:
        filters.append("-is:starred")

    # ---------------------------------------------------------
    # Label
    # ---------------------------------------------------------

    if label:
        filters.append(
            f"label:{label}"
        )

    # ---------------------------------------------------------
    # Folder
    # ---------------------------------------------------------

    if folder:

        folder_map = {
            "inbox": "in:inbox",
            "sent": "in:sent",
            "trash": "in:trash",
            "spam": "in:spam",
            "drafts": "in:drafts",
            "all": "in:anywhere",
        }

        folder_query = folder_map.get(
            folder.lower()
        )

        if folder_query:
            filters.append(folder_query)

    # ---------------------------------------------------------
    # Size filters
    # Gmail uses bytes.
    # ---------------------------------------------------------

    if larger_than is not None:
        filters.append(
            f"larger:{larger_than}"
        )

    if smaller_than is not None:
        filters.append(
            f"smaller:{smaller_than}"
        )

    # ---------------------------------------------------------
    # Raw Gmail query
    #
    # Allows advanced Gmail operators that we haven't
    # explicitly exposed as API parameters.
    # ---------------------------------------------------------

    if raw_query:
        filters.append(
            raw_query.strip()
        )

    return " ".join(
        filter(None, filters)
    )