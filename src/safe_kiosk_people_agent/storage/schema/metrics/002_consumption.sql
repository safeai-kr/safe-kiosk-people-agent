alter table metric_event add column consumed integer not null default 0 check(consumed in (0,1));
alter table metric_event add column collector_run_id text not null default '';
create index if not exists metric_event_pending on metric_event(consumed, source, spool_sequence);
create table if not exists scheduler_state (singleton integer primary key check(singleton=1), processed_through text not null, last_tick_at text not null);
create table if not exists health_journal (id integer primary key, source text not null, health text not null, observed_at text not null, collector_run_id text not null, reason text not null, consumed integer not null default 0);
