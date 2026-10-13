"""Exception hierarchy for the OCR subsystem."""


class OCRError(Exception):
    """Base class for all OCR errors."""


class CorruptFileError(OCRError):
    """Input file is empty, truncated or corrupted."""


class UnsupportedFormatError(OCRError):
    """File signature is not a supported PDF or image."""


class EncryptedFileError(OCRError):
    """PDF is password protected."""


class PageLimitExceededError(OCRError):
    """Document has more pages than the configured limit."""


class EngineCrashError(OCRError):
    """The underlying OCR engine failed or returned an unexpected shape."""
