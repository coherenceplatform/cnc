import os

import rudderstack.analytics as rudder_analytics
import machineid

rudder_analytics.write_key = "2eEyoetBjPLeYUOg8jRfOicBRiS"
rudder_analytics.dataPlaneUrl = "https://withcoherepvm.dataplane.rudderstack.com"
rudder_analytics.debug = True
rudder_analytics.gzip = True

# default to enabling telemetry for now
TELEMETRY_ENABLED = (
    False
    if os.environ.get("CNC_TELEMETRY_DISABLED")
    in [1, "1", "true", "True", "TRUE", "yes", "Y", "y", "Yes", "YES"]
    else True
)
CURRENT_COMMAND = ""


def send_event(command_name: str):
    command_data = {
        "name": command_name,
    }
    if TELEMETRY_ENABLED:
        try:
            _id = machineid.id()
        except Exception as e:
            print(f"Cannot get machine ID: {e}")
            _id = None

        try:
            user_id = os.environ.get("CNC_USER_ID", _id or "UNKNOWN")
            print(f"Sending {command_data} to RS for {user_id}")
            rudder_analytics.track(user_id, "command", command_data)
        except Exception as e:
            print(f"Cannot send telemetry event: {e}")
