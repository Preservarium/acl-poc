"""API routers."""

from app.api import auth, permissions, sites, plans, sensors, users, groups, brokers, alarms, alerts, dashboards, audit_logs

__all__ = [
    "auth",
    "permissions",
    "sites",
    "plans",
    "sensors",
    "brokers",
    "alarms",
    "alerts",
    "dashboards",
    "users",
    "groups",
    "audit_logs",
]
