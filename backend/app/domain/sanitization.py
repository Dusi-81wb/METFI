"""Dataset identifier and filesystem path security sanitization utilities."""

import re

# Strict alphanumeric, hyphen, and underscore identifier format (1-64 chars)
DATASET_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class DatasetIdValidationError(ValueError):
    """Raised when a dataset identifier fails security or path sanitization."""

    pass


def validate_dataset_id(dataset_id: str) -> str:
    """
    Validate and sanitize dataset identifier to prevent path traversal and arbitrary writes.

    Rules:
    - Must be non-empty string (1 to 64 characters).
    - Permitted characters: [a-zA-Z0-9_-] only.
    - Explicitly rejects: path traversal ('../', '..\\'), path separators ('/', '\\'),
      null bytes, whitespace, and special characters.

    Returns:
        The validated dataset_id string.

    Raises:
        DatasetIdValidationError: If validation fails.
    """
    if dataset_id is None or not isinstance(dataset_id, str):
        raise DatasetIdValidationError("Dataset ID must be a non-null string.")

    clean_id = dataset_id.strip()
    if not clean_id:
        raise DatasetIdValidationError("Dataset ID cannot be empty or blank.")

    if clean_id != dataset_id:
        raise DatasetIdValidationError(
            f"Dataset ID contains forbidden leading/trailing whitespace: '{dataset_id}'"
        )

    if "\0" in dataset_id:
        raise DatasetIdValidationError("Dataset ID contains null byte injection.")

    if "/" in dataset_id or "\\" in dataset_id or ".." in dataset_id:
        raise DatasetIdValidationError(
            f"Dataset ID contains path traversal or separator characters: '{dataset_id}'"
        )

    if not DATASET_ID_PATTERN.match(dataset_id):
        raise DatasetIdValidationError(
            f"Invalid dataset ID '{dataset_id}'. Must be 1-64 alphanumeric characters or [-_]."
        )

    return dataset_id
