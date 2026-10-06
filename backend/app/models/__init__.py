"""ORM model registry.

Importing this package imports every module's model file so that all tables
are registered on the single shared ``Base.metadata`` (see ``base.py``). Alembic
imports this package from ``alembic/env.py`` so ``--autogenerate`` can see the
full schema in one place.

Each module owns its own model file (see ``backend/guide.md``). As other
modules land, add their imports here, e.g.::

    from app.models import core      # noqa: F401  (farmers, farmlands, crops)
    from app.models import season    # noqa: F401  (M2)
    from app.models import state     # noqa: F401  (M3)
    from app.models import chat      # noqa: F401  (M5)
    from app.models import disease   # noqa: F401  (M6)

Only the Module 4 (weather) models exist on this branch for now.
"""

from app.models import weather  # noqa: F401  (M4: weather_events, weather_alerts)

__all__ = ["weather"]
