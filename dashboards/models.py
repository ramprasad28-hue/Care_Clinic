"""The dashboards app has no models.

Dashboards are read-mostly presentations over data owned by the ``accounts``,
``clinic`` and ``appointments`` apps. All state changes are delegated to the
existing transactional services in :mod:`appointments.services`, so no new
tables (and therefore no new migrations) are required (ADR-019).
"""
