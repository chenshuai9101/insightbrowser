"""InsightBrowser SDK — Custom Exceptions"""


class InsightBrowserError(Exception):
    """Base exception for InsightBrowser SDK."""
    pass


class SiteNotFoundError(InsightBrowserError):
    """Raised when a site is not found in the Registry."""
    pass


class ActionError(InsightBrowserError):
    """Raised when an action call fails."""

    def __init__(self, message: str, status_code: int = 500,
                 response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class ConnectionError(InsightBrowserError):
    """Raised when connection to a service fails."""
    pass


class ProtocolError(InsightBrowserError):
    """Raised when a response violates the AHP protocol."""
    pass
