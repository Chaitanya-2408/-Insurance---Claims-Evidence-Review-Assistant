from io import BytesIO

from pypdf import PdfReader


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt"
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def extract_document_text(file_storage):
    """
    Extract text from an uploaded PDF or TXT file.

    Returns:
        str: Extracted document text.

    Raises:
        ValueError: For unsupported, empty, oversized, or unreadable files.
    """

    if not file_storage:
        raise ValueError("No document was uploaded.")

    filename = (
        file_storage.filename or ""
    ).strip()

    if not filename:
        raise ValueError(
            "Uploaded document must have a filename."
        )

    extension = "." + filename.rsplit(".", 1)[-1].lower() \
        if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Only PDF and TXT files are supported."
        )

    file_storage.stream.seek(0)

    raw_data = file_storage.stream.read()

    if not raw_data:
        raise ValueError(
            f"{filename} is empty."
        )

    if len(raw_data) > MAX_FILE_SIZE:
        raise ValueError(
            f"{filename} exceeds the 5 MB file size limit."
        )

    try:

        if extension == ".txt":

            text = raw_data.decode(
                "utf-8",
                errors="replace"
            )

        else:

            reader = PdfReader(
                BytesIO(raw_data)
            )

            pages = []

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:
                    pages.append(page_text)

            text = "\n".join(pages)

    except Exception as error:

        raise ValueError(
            f"Unable to read {filename}: {error}"
        )

    text = text.strip()

    if not text:
        raise ValueError(
            f"No readable text was found in {filename}."
        )

    return text