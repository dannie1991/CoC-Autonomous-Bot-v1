from __future__ import annotations
import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone

log = logging.getLogger("cocbot")

def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")

def event(name: str, **fields) -> None:
    clean = {k: asdict(v) if is_dataclass(v) else v for k, v in fields.items()}
    payload = {"event": name, "ts": datetime.now(timezone.utc).isoformat(), **clean}
    log.info(json.dumps(payload, default=str, sort_keys=True))
