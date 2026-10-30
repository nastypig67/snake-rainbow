-- Run this once in Supabase: SQL Editor -> New query -> paste -> Run.
create table public.scores (
  id bigint generated always as identity primary key,
  nickname text not null check (char_length(nickname) between 1 and 12),
  score int not null check (score between 1 and 1000),
  created_at timestamptz not null default now()
);

create index scores_score_idx on public.scores (score desc);

-- Row Level Security: the public key can only read scores and add new ones.
alter table public.scores enable row level security;
create policy "anyone can read" on public.scores for select to anon using (true);
create policy "anyone can add" on public.scores for insert to anon with check (true);
grant select, insert on public.scores to anon;
