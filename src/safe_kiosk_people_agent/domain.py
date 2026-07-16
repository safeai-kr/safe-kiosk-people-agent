from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, Mapping
from uuid import UUID

class Source(StrEnum): WIFI='wifi'; BLE='ble'
class SourceHealth(StrEnum): HEALTHY='healthy'; DEGRADED='degraded'; RECOVERING='recovering'; UNAVAILABLE='unavailable'
class OutboxState(StrEnum): PENDING='pending'; DELIVERED='delivered'; TERMINAL_REJECTED='terminal_rejected'
@dataclass(frozen=True)
class NewObservationSummary: summary_id:str; source:Source; collector_run_id:str; device_token:str; window_start:datetime; window_end:datetime; first_observed_at:datetime; last_observed_at:datetime; sample_count:int; median_rssi_dbm:int; max_rssi_dbm:int; frequency_mhz:float|None; tx_power_dbm:int|None
@dataclass(frozen=True)
class StoredObservationSummary(NewObservationSummary): spool_sequence:int
@dataclass(frozen=True)
class SourceWatermark: source:Source; collector_run_id:str; boot_id:str; collector_started_at:datetime; caught_up_through:datetime; spool_sequence:int; health:SourceHealth; updated_at:datetime; updated_boottime_ns:int; progress_sequence:int
@dataclass(frozen=True)
class KismetCursor: generation_id:str; ts_sec:int; ts_usec:int; rowid:int
@dataclass(frozen=True)
class KismetPacket: generation_id:str; rowid:int; ts_sec:int; ts_usec:int; observed_at:datetime; transmitter_address:str; signal_dbm:int; frequency_mhz:float; tags:frozenset[str]
@dataclass(frozen=True)
class KismetGeneration: generation_id:str; path:Path; state:Literal['starting','active','closing','closed','consumed','quarantined']; boot_id:str; child_pid:int|None; child_pgid:int|None; child_start_ticks:int|None; created_at:datetime; closed_at:datetime|None; rotation_request_id:str|None
@dataclass(frozen=True)
class KismetProbe: generation_id:str; datasource:str; monitor_vif:str; progress_sequence:int; checked_boottime_ns:int; database_watermark:KismetCursor|None
class ClassificationLabel(StrEnum): UNKNOWN='unknown'; OUTSIDE='outside'; INSIDE='inside'
@dataclass(frozen=True)
class ProtocolThresholds: source:Source; inside_rssi_dbm:int; outside_rssi_dbm:int; state_confirmation_count:int
@dataclass(frozen=True)
class ClassificationState: confirmed:ClassificationLabel; candidate:ClassificationLabel|None; candidate_count:int; recent_samples:tuple[tuple[datetime,int],...]; last_observed_at:datetime|None
@dataclass(frozen=True)
class ClassificationUpdate: previous:ClassificationLabel; current:ClassificationLabel; changed:bool; median_rssi_dbm:int; observed_at:datetime; state:ClassificationState
@dataclass(frozen=True)
class SessionPolicy: session_timeout_seconds:int; min_dwell_seconds:int; max_dwell_seconds:int; fixed_mark_seconds:int=604800
@dataclass(frozen=True)
class TokenSession: source:Source; device_token:str; first_observed_at:datetime; last_observed_at:datetime; confirmed_state:ClassificationLabel; first_outside_at:datetime|None; first_inside_at:datetime|None; foot_counted:bool; entry_counted:bool; unconfirmed_entry:bool
@dataclass(frozen=True)
class FixedDeviceMark: source:Source; device_token:str; last_observed_at:datetime; fixed_until:datetime
@dataclass(frozen=True)
class SessionOutcome: source:Source; occurred_at:datetime; foot_traffic_count:int; entry_count:int; dwell_seconds_sum:Decimal; completed_dwell_session_count:int; timeout_closed_count:int; unconfirmed_entry_count:int; interrupted_session_count:int; quality_flags:tuple[str,...]
@dataclass(frozen=True)
class SessionTransition: session:TokenSession|None; outcomes:tuple[SessionOutcome,...]; fixed_mark:FixedDeviceMark|None
@dataclass(frozen=True)
class TickSourceHealth: wifi:SourceHealth; ble:SourceHealth
@dataclass(frozen=True)
class BucketSourceHealth: wifi:SourceHealth; ble:SourceHealth; quality_flags:tuple[str,...]
@dataclass(frozen=True)
class SourceCursor: source:Source; collector_run_id:str; spool_sequence:int; last_event_time:datetime|None
@dataclass(frozen=True)
class MetricEvent: source:Source; summary_id:str; spool_sequence:int; event_time:datetime; summary:StoredObservationSummary
@dataclass(frozen=True)
class CommitOutcome: applied:bool; source_cursor:SourceCursor; affected_bucket_starts:tuple[datetime,...]
@dataclass(frozen=True)
class ActionOutcome: kind:Literal['event','health','tick']; at:datetime; applied:bool; source_cursor:SourceCursor|None; affected_bucket_starts:tuple[datetime,...]
@dataclass(frozen=True)
class ProtocolSourceDetail: inside_tick_count:int; foot_traffic_count:int; entry_count:int; dwell_seconds_sum:Decimal; completed_dwell_session_count:Decimal; timeout_closed_count:int; unconfirmed_entry_count:int; interrupted_session_count:int
@dataclass(frozen=True)
class ProtocolBucket: bucket_start:datetime; bucket_end:datetime; fused_inside_ticks:tuple[int|None,...]; source_detail:Mapping[Source,ProtocolSourceDetail]; observation_counts:Mapping[Source,int]; quality_flags:tuple[str,...]
@dataclass(frozen=True)
class StateSnapshot: snapshot_at:datetime; processed_through:datetime; source_cursors:Mapping[Source,SourceCursor]; canonical_state_json:str; config_generation:int
@dataclass(frozen=True)
class ConfigSnapshot: generation:int; threshold_version:str; content_digest:str; effective_at:datetime; canonical_config_json:str
@dataclass(frozen=True)
class BucketMetric:
    bucket_start:datetime; bucket_end:datetime; estimated_people_count:int; peak_people_count:int; foot_traffic_count:int; entry_count:int; dwell_seconds_sum:Decimal; completed_dwell_session_count:Decimal; wifi_observation_count:int; ble_observation_count:int; confidence_score:Decimal; quality_flags:tuple[str,...]; source_detail:Mapping[Source,ProtocolSourceDetail]; threshold_version:str; metric_version:str; revision:int; generated_at:datetime
    def to_wire(self)->Mapping[str,object]: return {'bucket_start':self.bucket_start.isoformat(),'bucket_end':self.bucket_end.isoformat(),'estimated_people_count':self.estimated_people_count,'peak_people_count':self.peak_people_count,'foot_traffic_count':self.foot_traffic_count,'entry_count':self.entry_count,'dwell_seconds_sum':str(self.dwell_seconds_sum),'completed_dwell_session_count':str(self.completed_dwell_session_count),'wifi_observation_count':self.wifi_observation_count,'ble_observation_count':self.ble_observation_count,'confidence_score':str(self.confidence_score),'quality_flags':list(self.quality_flags),'threshold_version':self.threshold_version,'metric_version':self.metric_version,'revision':self.revision,'generated_at':self.generated_at.isoformat()}
@dataclass(frozen=True)
class LateQuarantineRecord: event:MetricEvent; reason:Literal['late_beyond_horizon']; quarantined_at:datetime
@dataclass(frozen=True)
class ReplayResult: applied:bool; reason:str|None; rebuilt_buckets:tuple[BucketMetric,...]; affected_bucket_starts:tuple[datetime,...]; terminal_snapshot:StateSnapshot|None; quarantined_events:tuple[LateQuarantineRecord,...]
@dataclass(frozen=True)
class IngestBucketResult: index:int; bucket_start:datetime|None; revision:int|None; result:Literal['inserted','updated','duplicate','superseded','rejected']; reason:str|None
@dataclass(frozen=True)
class IngestResponse: sensor_id:UUID; received_at:datetime; status_result:Literal['inserted','updated','stale']; results:tuple[IngestBucketResult,...]
@dataclass(frozen=True)
class SensorError: component:str; code:str; message:str; occurred_at:datetime
@dataclass(frozen=True)
class ComponentStatus: component:str; health:SourceHealth; error:SensorError|None; latched:bool; boot_id:str; sequence:int; observed_at:datetime; observed_boottime_ns:int
@dataclass(frozen=True)
class SensorStatus:
    observed_at:datetime; kismet_status:SourceHealth; wifi_status:SourceHealth; ble_status:SourceHealth; metrics_status:SourceHealth; upload_status:SourceHealth; last_wifi_observed_at:datetime|None; last_ble_observed_at:datetime|None; last_bucket_created_at:datetime|None; last_upload_at:datetime|None; recovery_counts:Mapping[str,int]; cpu_percent:Decimal; memory_bytes:int; disk_free_bytes:int; pending_outbox_count:int; last_error:SensorError|None; threshold_version:str; metric_version:str
    def to_wire(self)->Mapping[str,object]: return {'observed_at':self.observed_at.isoformat(),'kismet_status':self.kismet_status.value,'wifi_status':self.wifi_status.value,'ble_status':self.ble_status.value,'metrics_status':self.metrics_status.value,'upload_status':self.upload_status.value,'recovery_counts':dict(self.recovery_counts),'cpu_percent':str(self.cpu_percent),'memory_bytes':self.memory_bytes,'disk_free_bytes':self.disk_free_bytes,'pending_outbox_count':self.pending_outbox_count,'threshold_version':self.threshold_version,'metric_version':self.metric_version}
    def watchdog_message(self)->str: return f"kismet={self.kismet_status.value} wifi={self.wifi_status.value} ble={self.ble_status.value} metrics={self.metrics_status.value} upload={self.upload_status.value}"
@dataclass(frozen=True)
class UploadRunResult: metrics_sent:int; delivered:tuple[datetime,...]; terminal_rejected:tuple[datetime,...]; retry_pending:bool; credential_error:bool; health_heartbeat_sent:bool
@dataclass(frozen=True)
class HealthEvent: source:Source; health:SourceHealth; observed_at:datetime; collector_run_id:str; reason:str
@dataclass(frozen=True)
class ScheduledAction: kind:Literal['event','health','tick']; at:datetime; source:Source|None; spool_sequence:int; payload:Any
@dataclass(frozen=True)
class EventPartition: on_time:tuple[MetricEvent,...]; late:tuple[MetricEvent,...]
@dataclass(frozen=True)
class ReductionBatch: session_rows:tuple[Mapping[str,object],...]; fixed_device_rows:tuple[Mapping[str,object],...]; health_rows:tuple[Mapping[str,object],...]; bucket_rows:tuple[BucketMetric,...]; snapshot_rows:tuple[Mapping[str,object],...]; outbox_rows:tuple[Mapping[str,object],...]
@dataclass(frozen=True)
class MetricsRunResult: health_events:tuple[HealthEvent,...]; action_outcomes:tuple[ActionOutcome,...]; replay_outcomes:tuple[ReplayResult,...]; closed_buckets:tuple[BucketMetric,...]; interrupted_session_count:int; status:SensorStatus
