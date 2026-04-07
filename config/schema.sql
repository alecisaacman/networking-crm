create table if not exists contacts (
    id integer primary key,
    full_name text not null,
    company text,
    role_title text,
    location text,
    source text,
    email text,
    linkedin_url text,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp
);

create table if not exists notes (
    id integer primary key,
    contact_id integer not null,
    body text not null,
    created_at text not null default current_timestamp,
    foreign key (contact_id) references contacts (id) on delete cascade
);

create table if not exists follow_ups (
    id integer primary key,
    contact_id integer not null,
    due_on text not null,
    status text not null default 'pending',
    reason text,
    created_at text not null default current_timestamp,
    completed_at text,
    foreign key (contact_id) references contacts (id) on delete cascade
);
