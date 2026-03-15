-- ==============================================================================
-- 工业软件智能售后助手 - Full Database Schema Setup
-- 适用环境: Supabase (PostgreSQL 15+)
-- 描述: 一键部署所有数据库表、RLS策略、函数和触发器。
-- ==============================================================================

-- 1. 清理旧对象
-- 使用 CASCADE 会自动删除依赖于表的 Triggers 和 Foreign Keys
drop table if exists public.feedback cascade;
drop table if exists public.chat_messages cascade;
drop table if exists public.chat_sessions cascade;
drop table if exists public.profiles cascade;

-- 只需要清理挂在 auth.users (系统表) 上的 trigger，因为它不会被 drop
drop trigger if exists on_auth_user_created on auth.users;

-- 清理函数
drop function if exists public.handle_new_user();
drop function if exists public.update_session_timestamp();
drop function if exists public.increment_query_count();
drop function if exists public.increment_feedback_count();
drop function if exists public.is_admin();

-- ==========================================
-- 2. 建表: Profiles (用户档案 & 统计)
-- ==========================================
create table public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  email text,
  display_name text,
  role text default 'user' check (role in ('admin', 'user')),
  department text,
  status text default 'active',
  preferences jsonb default '{}'::jsonb,
  -- 统计字段
  stats jsonb default '{"total_queries": 0, "total_feedback_given": 0}'::jsonb,
  created_at timestamptz default now()
);

alter table public.profiles enable row level security;

-- 辅助函数: 安全检查管理员权限
create or replace function public.is_admin()
returns boolean as $$
begin
  return exists (
    select 1 from public.profiles
    where id = auth.uid() and role = 'admin'
  );
end;
$$ language plpgsql security definer;

-- Profiles 策略
create policy "Users can view own profile" 
  on public.profiles for select using ( auth.uid() = id );

create policy "Admins can view all profiles"
  on public.profiles for select using ( public.is_admin() );

create policy "Users can update own profile"
  on public.profiles for update using ( auth.uid() = id );

create policy "Admins can update profiles"
  on public.profiles for update using ( public.is_admin() );

-- ==========================================
-- 3. 建表: Chat Sessions
-- ==========================================
create table public.chat_sessions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  title text default '新对话',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.chat_sessions enable row level security;

create policy "Users can view own sessions"
  on public.chat_sessions for select using ( auth.uid() = user_id );

create policy "Users can delete own sessions"
  on public.chat_sessions for delete using ( auth.uid() = user_id );

create policy "Users can insert own sessions"
  on public.chat_sessions for insert with check ( auth.uid() = user_id );

-- ==========================================
-- 4. 建表: Chat Messages
-- ==========================================
create table public.chat_messages (
  id uuid default gen_random_uuid() primary key,
  session_id uuid references public.chat_sessions(id) on delete cascade not null,
  user_id uuid references public.profiles(id) on delete cascade not null,
  role text check (role in ('user', 'assistant')),
  content text,
  sources jsonb,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

alter table public.chat_messages enable row level security;

create policy "Users can view own messages"
  on public.chat_messages for select using ( auth.uid() = user_id );

create policy "Users can insert own messages"
  on public.chat_messages for insert with check ( auth.uid() = user_id );

-- ==========================================
-- 5. 建表: Feedback
-- ==========================================
create table public.feedback (
  id uuid default gen_random_uuid() primary key,
  message_id uuid references public.chat_messages(id) on delete cascade not null,
  user_id uuid references public.profiles(id) on delete cascade not null,
  score int check (score in (1, -1)),
  comment text,
  created_at timestamptz default now()
);

alter table public.feedback enable row level security;

create policy "Users can insert own feedback"
  on public.feedback for insert with check ( auth.uid() = user_id );

create policy "Users can view own feedback"
  on public.feedback for select using ( auth.uid() = user_id );

-- ==========================================
-- 6. 配置 SDK 自动化逻辑
-- ==========================================

-- 6.1 用户注册 -> 自动创建 Profile
create or replace function public.handle_new_user() 
returns trigger as $$
begin
  insert into public.profiles (id, email, display_name)
  values (new.id, new.email, split_part(new.email, '@', 1));
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- 6.2 新消息 -> 更新 Session 时间
create or replace function public.update_session_timestamp()
returns trigger as $$
begin
    update public.chat_sessions
    set updated_at = now()
    where id = new.session_id;
    return new;
end;
$$ language plpgsql;

create trigger on_new_message
    after insert on public.chat_messages
    for each row execute procedure public.update_session_timestamp();

-- 6.3 用户提问 -> 统计+1
create or replace function public.increment_query_count()
returns trigger as $$
begin
    if new.role = 'user' then
        update public.profiles
        set stats = jsonb_set(
            coalesce(stats, '{}'::jsonb), 
            '{total_queries}', 
            (coalesce((stats->>'total_queries')::int, 0) + 1)::text::jsonb
        )
        where id = new.user_id;
    end if;
    return new;
end;
$$ language plpgsql;

create trigger on_user_query
    after insert on public.chat_messages
    for each row execute procedure public.increment_query_count();

-- 6.4 用户反馈 -> 统计+1
create or replace function public.increment_feedback_count()
returns trigger as $$
begin
    update public.profiles
    set stats = jsonb_set(
        coalesce(stats, '{}'::jsonb), 
        '{total_feedback_given}', 
        (coalesce((stats->>'total_feedback_given')::int, 0) + 1)::text::jsonb
    )
    where id = new.user_id;
    return new;
end;
$$ language plpgsql;

create trigger on_user_feedback
    after insert on public.feedback
    for each row execute procedure public.increment_feedback_count();

-- ==========================================
-- 7. 修复孤儿用户 (可选)
-- ==========================================
insert into public.profiles (id, email, display_name)
select id, email, split_part(email, '@', 1)
from auth.users
where id not in (select id from public.profiles)
on conflict do nothing;
