"""Authorized queries over shared event logs."""
from datetime import datetime
from .models import Result

class HistoricalDataManagement:
    def __init__(self, store, access):
        self.__store = store
        self.__access = access

    def record_event(self, event_type, description):
        if not isinstance(event_type, str) or not event_type.strip() or not isinstance(description, str):
            return Result(False, "Invalid event")
        self.__store.log(event_type, description)
        return Result(True, "Event recorded")

    def search(self, token, adc_id=None, event_type=None, start=None, end=None):
        if not self.__access.authorize(token, "history:view"):
            return Result(False, "Access denied")
        return self.__search_records(adc_id, event_type, start, end)

    def __search_records(self, adc_id, event_type, start, end):
        for dt in (start, end):
            if dt is not None and (not isinstance(dt, datetime) or dt.tzinfo is None):
                return Result(False, "Dates must be timezone-aware datetimes")
        if start is not None and end is not None and start > end:
            return Result(False, "Start is after end")
        events = []
        try:
            for event in self.__store.get_events():
                when = datetime.fromisoformat(event["time"])
                # Description-based matching is a limitation of current storage schema.
                if adc_id is not None and adc_id not in event["description"]:
                    continue
                if event_type is not None and event["type"] != event_type:
                    continue
                if start is not None and when < start:
                    continue
                if end is not None and when > end:
                    continue
                events.append(event)
        except (KeyError, ValueError, TypeError) as exc:
            return Result(False, "Malformed event: " + str(exc))
        return Result(True, "Events retrieved" if events else "No matching records", {"events": events})

    def search_for_reporting(self, token, **filters):
        # Reports require BOTH reports:view and history:view.
        if not self.__access.authorize(token, "reports:view"):
            return Result(False, "Access denied")
        return self.search(token, **filters)
