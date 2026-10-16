"""Website application: public, read-only pages (home, specialities, doctors).

Kept separate from ``clinic`` per ``docs/architecture.md`` §2.1 so the domain
app owns models/admin while presentation of the public catalog lives here. The
allowed dependency direction is ``website -> clinic`` and ``website -> accounts``.
"""
