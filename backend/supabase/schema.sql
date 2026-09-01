-- Run this once in the Supabase SQL editor (Project → SQL Editor → New query).
-- Creates the tables the FastAPI backend reads/writes via DATABASE_URL.

create table if not exists profiles (
  id bigint generated always as identity primary key,
  name text not null,
  niche text not null,
  keywords jsonb not null default '[]'::jsonb,
  exclude_keywords jsonb not null default '[]'::jsonb,
  experience text,
  model text not null default 'groq',
  min_job_score integer not null default 40,
  is_active boolean not null default false,
  created_at timestamptz not null default now()
);

-- One scraped job per (profile, upwork job id). Re-scraping the same job for the
-- same profile updates it in place (bumps scraped_at) instead of duplicating it.
create table if not exists jobs (
  profile_id bigint not null references profiles(id) on delete cascade,
  job_id text not null,
  title text,
  url text,
  description text,
  skills text,
  category_name text,
  subcategory_name text,
  price_type text,
  price numeric,
  price_min numeric,
  price_max numeric,
  experience_level text,
  client_location text,
  buyer_payment_verified boolean,
  buyer_score numeric,
  hire_rate numeric,
  total_spent numeric,
  date_posted timestamptz,
  job_score numeric,
  -- Signals the proposal writer needs: client strength, and the application
  -- instructions clients use to filter out copy-paste applicants.
  open_jobs integer,
  avg_hourly_rate numeric,
  questions jsonb,
  ai_specific_requirements_before_applying text,
  ai_anti_bot_phrase text,
  scraped_at timestamptz not null default now(),
  primary key (profile_id, job_id)
);

create index if not exists jobs_profile_scraped_idx on jobs (profile_id, scraped_at desc);

-- Safe to re-run on an existing database.
alter table jobs add column if not exists open_jobs integer;
alter table jobs add column if not exists avg_hourly_rate numeric;
alter table jobs add column if not exists questions jsonb;
alter table jobs add column if not exists ai_specific_requirements_before_applying text;
alter table jobs add column if not exists ai_anti_bot_phrase text;
