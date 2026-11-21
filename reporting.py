"""Reports are derived from HistoricalDataManagement, not a separate log."""
from collections import Counter
from .models import Result

class Reporting:
    def __init__(self, history):
        self.__history = history

    def generate(self, token, start=None, end=None, adc_id=None):
        result = self.__history.search_for_reporting(token, adc_id=adc_id, start=start, end=end)
        if not result.ok:
            return result
        events = result.data["events"]
        if not events:
            return Result(False, "No matching records")
        return Result(True, "Report generated", {
            "total_events": len(events),
            "events_by_type": dict(Counter(event["type"] for event in events)),
            "events": events
        })
