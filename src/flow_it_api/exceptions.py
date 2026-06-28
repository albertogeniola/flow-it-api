"""Exceptions for the FlowIt VMC API."""


class FlowItError(Exception):
    """Base exception for flow-it-api."""


class FlowItAuthError(FlowItError):
    """Exception raised for authentication errors."""


class FlowItConnectionError(FlowItError):
    """Exception raised for connection errors."""


class FlowItResponseError(FlowItError):
    """Exception raised for invalid or error responses from the device."""


class FlowItCommandError(FlowItError):
    """Exception raised when a command fails."""
