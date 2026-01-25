from datetime import datetime, timezone

import pytest

from src.application.api_use_cases import EventUseCase
from src.domain.entities import Event
from src.domain.exceptions import ResourceNotFound


class FakeCalendarTool:
	def __init__(self) -> None:
		self.events: dict[str, Event] = {}

	def create_event(self, *, user_id: str, title: str, starts_at: datetime, ends_at: datetime, metadata=None) -> Event:
		event = Event(
			id=f"evt_{len(self.events) + 1}",
			user_id=user_id,
			title=title,
			starts_at=starts_at,
			ends_at=ends_at,
		)
		self.events[event.id] = event
		return event

	def list_events(self, user_id: str) -> list[Event]:
		return [evt for evt in self.events.values() if evt.user_id == user_id]

	def get_event(self, *, event_id: str, user_id: str):
		event = self.events.get(event_id)
		if not event:
			return None
		return event

	def update_event(self, *, event_id: str, title=None, starts_at=None, ends_at=None):
		event = self.events.get(event_id)
		if not event:
			return None
		if title is not None:
			event.title = title
		if starts_at is not None:
			event.starts_at = starts_at
		if ends_at is not None:
			event.ends_at = ends_at
		return event

	def delete_event(self, event_id: str) -> bool:
		return self.events.pop(event_id, None) is not None


def test_event_use_case_crud() -> None:
	calendar = FakeCalendarTool()
	use_case = EventUseCase(calendar_tool=calendar)
	start = datetime.now(tz=timezone.utc)
	end = start

	created = use_case.create(user_id="user-1", title="demo", starts_at=start, ends_at=end)
	assert created.title == "demo"

	listed = use_case.list(user_id="user-1")
	assert len(listed) == 1

	updated = use_case.update(
		event_id=created.id,
		user_id="user-1",
		title="nuevo",
		starts_at=None,
		ends_at=None,
	)
	assert updated.title == "nuevo"

	use_case.delete(event_id=created.id, user_id="user-1")
	assert use_case.list(user_id="user-1") == []

	with pytest.raises(ResourceNotFound):
		use_case.get(event_id=created.id, user_id="user-1")
