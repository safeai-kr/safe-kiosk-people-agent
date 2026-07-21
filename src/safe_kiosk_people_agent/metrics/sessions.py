from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from ..domain import (
    ClassificationLabel,
    FixedDeviceMark,
    SessionOutcome,
    SessionPolicy,
    SessionTransition,
    Source,
    TokenSession,
)


class SessionEngine:
    def __init__(self, policy: SessionPolicy) -> None:
        if policy.session_timeout_seconds <= 0 or policy.min_dwell_seconds < 0:
            raise ValueError("invalid session policy")
        if policy.min_dwell_seconds > policy.max_dwell_seconds:
            raise ValueError("min dwell must not exceed max dwell")
        self.policy = policy
        self.sessions: dict[tuple[Source, str], TokenSession] = {}
        self.fixed_marks: dict[tuple[Source, str], FixedDeviceMark] = {}
        self._last_observation: dict[tuple[Source, str], datetime] = {}

    @staticmethod
    def _at(value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value.astimezone(timezone.utc)

    def _outcome(self, source: Source, at: datetime, **values: object) -> SessionOutcome:
        defaults: dict[str, object] = {
            "foot_traffic_count": 0,
            "entry_count": 0,
            "dwell_seconds_sum": Decimal(0),
            "completed_dwell_session_count": 0,
            "timeout_closed_count": 0,
            "unconfirmed_entry_count": 0,
            "interrupted_session_count": 0,
            "quality_flags": (),
        }
        defaults.update(values)
        return SessionOutcome(source, at, **defaults)  # type: ignore[arg-type]

    def apply_observation(
        self, source: Source, device_token: str, observed_at: datetime, state: ClassificationLabel
    ) -> SessionTransition:
        observed_at = self._at(observed_at)
        key = (source, device_token)
        mark = self.fixed_marks.get(key)
        if mark is not None and observed_at <= mark.fixed_until:
            return SessionTransition(None, (), mark)
        if mark is not None:
            self.fixed_marks.pop(key, None)
        if state is ClassificationLabel.UNKNOWN:
            return SessionTransition(self.sessions.get(key), (), None)
        current = self.sessions.get(key)
        if current is None:
            first_inside = observed_at if state is ClassificationLabel.INSIDE else None
            current = TokenSession(source, device_token, observed_at, observed_at, state, observed_at if state is ClassificationLabel.OUTSIDE else None, first_inside, False, False, state is ClassificationLabel.INSIDE)
            self.sessions[key] = current
            self._last_observation[key] = observed_at
            return SessionTransition(current, (), None)

        outcomes: list[SessionOutcome] = []
        if state is ClassificationLabel.INSIDE and current.confirmed_state is ClassificationLabel.OUTSIDE and not current.entry_counted:
            outcomes.append(self._outcome(source, observed_at, foot_traffic_count=1, entry_count=1))
            current = replace(current, entry_counted=True, foot_counted=True, first_inside_at=current.first_inside_at or observed_at)
        if state is ClassificationLabel.INSIDE and current.first_inside_at is None:
            current = replace(current, first_inside_at=observed_at, unconfirmed_entry=True)
        if state is ClassificationLabel.OUTSIDE and current.first_outside_at is None:
            current = replace(current, first_outside_at=observed_at)
        current = replace(current, last_observed_at=observed_at, confirmed_state=state)
        if current.first_inside_at is not None and observed_at - current.first_observed_at > timedelta(seconds=self.policy.max_dwell_seconds):
            mark = FixedDeviceMark(source, device_token, observed_at, observed_at + timedelta(seconds=self.policy.fixed_mark_seconds))
            self.fixed_marks[key] = mark
            self.sessions.pop(key, None)
            self._last_observation[key] = observed_at
            return SessionTransition(None, tuple(outcomes), mark)
        self.sessions[key] = current
        self._last_observation[key] = observed_at
        return SessionTransition(current, tuple(outcomes), None)

    def _close(self, key: tuple[Source, str], now: datetime, *, interrupted: bool = False) -> SessionOutcome | None:
        session = self.sessions.pop(key, None)
        if session is None:
            return None
        if interrupted:
            return self._outcome(session.source, now, interrupted_session_count=1, quality_flags=("source_outage_interrupted",))
        duration = Decimal(0)
        completed = 0
        if session.first_inside_at is not None:
            seconds = (session.last_observed_at - session.first_inside_at).total_seconds()
            if self.policy.min_dwell_seconds <= seconds <= self.policy.max_dwell_seconds:
                duration = Decimal(str(seconds))
                completed = 1
        foot = 0 if session.foot_counted else 1 if session.first_outside_at is not None else 0
        unconfirmed = 1 if session.unconfirmed_entry and not session.entry_counted else 0
        return self._outcome(session.source, now, foot_traffic_count=foot, dwell_seconds_sum=duration, completed_dwell_session_count=completed, timeout_closed_count=1, unconfirmed_entry_count=unconfirmed)

    def close_timeouts(self, now: datetime) -> tuple[SessionOutcome, ...]:
        now = self._at(now)
        result = []
        for key, session in tuple(self.sessions.items()):
            if now - session.last_observed_at >= timedelta(seconds=self.policy.session_timeout_seconds):
                outcome = self._close(key, now)
                if outcome is not None:
                    result.append(outcome)
        return tuple(result)

    def interrupt_source(self, source: Source, occurred_at: datetime) -> tuple[SessionOutcome, ...]:
        occurred_at = self._at(occurred_at)
        result = []
        for key in tuple(self.sessions):
            if key[0] == source:
                outcome = self._close(key, occurred_at, interrupted=True)
                if outcome is not None:
                    result.append(outcome)
        return tuple(result)

    def expire_fixed_marks(self, now: datetime) -> tuple[FixedDeviceMark, ...]:
        now = self._at(now)
        expired = tuple(mark for key, mark in self.fixed_marks.items() if now > mark.fixed_until)
        for mark in expired:
            self.fixed_marks.pop((mark.source, mark.device_token), None)
        return expired
