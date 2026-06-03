"""Catalog of permission codes used by `requires(...)` and seeded into the DB.

Format: <resource>:<verb>[:<scope>]
Scope: 'own' (only the user's own rows) or 'any' (admin).
"""

from __future__ import annotations

# Per-resource standard CRUD
PERM_BEAN_READ          = "bean:read"
PERM_BEAN_CREATE        = "bean:create"
PERM_BEAN_UPDATE_OWN    = "bean:update:own"
PERM_BEAN_UPDATE_ANY    = "bean:update:any"
PERM_BEAN_DELETE_OWN    = "bean:delete:own"
PERM_BEAN_DELETE_ANY    = "bean:delete:any"

PERM_BREWLOG_READ        = "brewlog:read"
PERM_BREWLOG_CREATE      = "brewlog:create"
PERM_BREWLOG_UPDATE_OWN  = "brewlog:update:own"
PERM_BREWLOG_UPDATE_ANY  = "brewlog:update:any"
PERM_BREWLOG_DELETE_OWN  = "brewlog:delete:own"
PERM_BREWLOG_DELETE_ANY  = "brewlog:delete:any"

PERM_EQUIPMENT_READ        = "equipment:read"
PERM_EQUIPMENT_CREATE      = "equipment:create"
PERM_EQUIPMENT_UPDATE_OWN  = "equipment:update:own"
PERM_EQUIPMENT_UPDATE_ANY  = "equipment:update:any"
PERM_EQUIPMENT_DELETE_OWN  = "equipment:delete:own"
PERM_EQUIPMENT_DELETE_ANY  = "equipment:delete:any"

PERM_ROASTER_READ        = "roaster:read"
PERM_ROASTER_CREATE      = "roaster:create"
PERM_ROASTER_UPDATE_OWN  = "roaster:update:own"
PERM_ROASTER_UPDATE_ANY  = "roaster:update:any"
PERM_ROASTER_DELETE_OWN  = "roaster:delete:own"
PERM_ROASTER_DELETE_ANY  = "roaster:delete:any"

# Cross-cutting
PERM_USER_LIST    = "user:list"
PERM_USER_OBSERVE = "user:observe"
PERM_USER_RESET   = "user:reset"
PERM_LOG_READ     = "log:read"
PERM_SECURITY_ANALYZE = "security:analyze"
PERM_CHAT_SEND    = "chat:send"
PERM_CHAT_READ    = "chat:read"
PERM_GENERATOR    = "generator:control"  # admin-only Faker generator

ALL_PERMISSIONS: list[str] = [
    PERM_BEAN_READ, PERM_BEAN_CREATE, PERM_BEAN_UPDATE_OWN, PERM_BEAN_UPDATE_ANY,
    PERM_BEAN_DELETE_OWN, PERM_BEAN_DELETE_ANY,
    PERM_BREWLOG_READ, PERM_BREWLOG_CREATE, PERM_BREWLOG_UPDATE_OWN, PERM_BREWLOG_UPDATE_ANY,
    PERM_BREWLOG_DELETE_OWN, PERM_BREWLOG_DELETE_ANY,
    PERM_EQUIPMENT_READ, PERM_EQUIPMENT_CREATE, PERM_EQUIPMENT_UPDATE_OWN, PERM_EQUIPMENT_UPDATE_ANY,
    PERM_EQUIPMENT_DELETE_OWN, PERM_EQUIPMENT_DELETE_ANY,
    PERM_ROASTER_READ, PERM_ROASTER_CREATE, PERM_ROASTER_UPDATE_OWN, PERM_ROASTER_UPDATE_ANY,
    PERM_ROASTER_DELETE_OWN, PERM_ROASTER_DELETE_ANY,
    PERM_USER_LIST, PERM_USER_OBSERVE, PERM_USER_RESET, PERM_LOG_READ, PERM_SECURITY_ANALYZE,
    PERM_CHAT_SEND, PERM_CHAT_READ, PERM_GENERATOR,
]
