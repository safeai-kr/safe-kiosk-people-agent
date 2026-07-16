alter table observation_summary add column spool_sequence integer;
create unique index if not exists observation_summary_spool_sequence on observation_summary(spool_sequence);
