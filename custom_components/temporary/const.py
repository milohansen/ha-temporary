"""Constants for the Temporary Entities integration."""

# Integration domain
DOMAIN = "temporary"

# Version
VERSION = "0.1.0"

# Platforms
PLATFORMS = []

# Configuration keys
CONF_MIN_PERSIST_DURATION = "min_persist_duration"
CONF_CLEANUP_INTERVAL = "cleanup_interval"
CONF_FINALIZED_GRACE_PERIOD = "finalized_grace_period"
CONF_INACTIVE_MAX_AGE = "inactive_max_age"

# Default values
DEFAULT_MIN_PERSIST_DURATION = (
    60  # seconds - entities shorter than this won't be saved to disk
)
DEFAULT_CLEANUP_INTERVAL = (
    300  # seconds (5 minutes) - how often to check for expired entities
)
DEFAULT_FINALIZED_GRACE_PERIOD = (
    30  # seconds - how long to keep finalized entities before cleanup
)
DEFAULT_INACTIVE_MAX_AGE = (
    86400  # seconds (24 hours) - how long to keep paused/inactive entities
)

# State constants
STATE_ACTIVE = "active"
STATE_PAUSED = "paused"
STATE_FINALIZED = "finalized"
STATE_IDLE = "idle"

# Attribute keys
ATTR_CREATED_AT = "created_at"
ATTR_FINALIZED_AT = "finalized_at"
ATTR_EXPECTED_DURATION = "expected_duration"
ATTR_STATE = "state"
ATTR_DURATION = "duration"
ATTR_REMAINING = "remaining"
ATTR_FINISHES_AT = "finishes_at"

# Service names
SERVICE_DELETE = "delete"
SERVICE_PAUSE = "pause"
SERVICE_RESUME = "resume"
SERVICE_CREATE_TEMPORARY = "create_temporary"
SERVICE_START = "start"
SERVICE_CANCEL = "cancel"
SERVICE_FINISH = "finish"
