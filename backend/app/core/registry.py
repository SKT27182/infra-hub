"""
Service registry for dynamic service discovery.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base import BaseService


class ServiceRegistry:
    """Central registry for all managed services."""

    _services: dict[str, "BaseService"] = {}

    @classmethod
    def register(cls, service: "BaseService") -> None:
        """Register a service."""
        cls._services[service.name] = service

    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister a service by name."""
        cls._services.pop(name, None)

    @classmethod
    def get(cls, name: str) -> "BaseService | None":
        """Get a service by name."""
        return cls._services.get(name)

    @classmethod
    def all(cls) -> list["BaseService"]:
        """Get all registered services."""
        return list(cls._services.values())

    @classmethod
    def names(cls) -> list[str]:
        """Get all registered service names."""
        return list(cls._services.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered services."""
        cls._services.clear()
