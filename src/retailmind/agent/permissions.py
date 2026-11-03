"""RetailMind AI — Executable Permission Layer (ask_on_write)."""

from typing import Any, Callable, Dict, Optional


class PermissionManager:
    """Enforces human-in-the-loop authorization on state-changing operations."""

    def __init__(self, policy: str = "ask_on_write"):
        self.policy = policy  # "auto" | "ask_on_write" | "always_ask"

    def check_permission(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        approval_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
    ) -> bool:
        """Determines whether a tool call is permitted to execute.

        Returns True if authorized, False otherwise.
        """
        # Read-only tools always execute automatically under ask_on_write
        if tool_name != "generate_report":
            if self.policy == "always_ask":
                return approval_callback(tool_name, arguments) if approval_callback else False
            return True

        # Tool is generate_report (WRITE ACTION)
        if self.policy == "auto":
            return True

        # ask_on_write policy requires explicit approval
        if approval_callback is not None:
            return bool(approval_callback(tool_name, arguments))

        # If no callback provided, write operation is denied by default
        return False
