"""
Admin-facing data: the saved error log and the admin audit trail.

Owns the bot layer's access to the errors and admin_audit tables. See
user_service for why these are re-exports rather than wrappers.

The audit write is reached from `require_admin()` in the bot layer, which is
the single gate every admin command passes through — see v3.7.8, where slash
commands were bypassing the audit that menu actions recorded.
"""

from app.database.repositories import (
    clear_errors,
    get_recent_errors,
    save_admin_audit,
)

__all__ = ["clear_errors", "get_recent_errors", "save_admin_audit"]
