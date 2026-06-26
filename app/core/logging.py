# import logging

# from app.core.config import settings


# logging.basicConfig(
#     level=settings.LOG_LEVEL,
#     format="%(asctime)s | %(levelname)s | %(message)s",
# )

# logger = logging.getLogger("MediGuardian")
import logging

from app.core.config import settings
from app.core.constants import LOG_FORMAT


logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=LOG_FORMAT,
)

logger = logging.getLogger("MediGuardian")