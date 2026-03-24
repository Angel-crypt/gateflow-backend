```dbml
// GateFlow — Database Schema
// https://dbdiagram.io

Table destinations_industrialpark {
  id          integer     [pk, increment]
  name        varchar(100)
  address     text        [note: 'blank=True']
  created_at  datetime
  is_active   boolean     [default: true]
}

Table destinations_destination {
  id              integer     [pk, increment]
  name            varchar(100)
  type            varchar(10) [note: '"company" | "area"']
  is_active       boolean     [default: true]
  park_id         integer     [ref: > destinations_industrialpark.id, note: 'CASCADE']
  responsible_id  integer     [ref: > users_user.id, note: 'SET_NULL', null]
}

Table users_user {
  id           integer     [pk, increment]
  email        varchar     [unique]
  username     varchar(150) [note: 'blank=True']
  first_name   varchar(150)[note: 'blank=True']
  last_name    varchar(150)[note: 'blank=True']
  role         varchar(20) [note: '"admin" | "guard" | "tenant"']
  is_active    boolean     [default: true]
  is_staff     boolean     [default: false]
  is_superuser boolean     [default: false]
  date_joined  datetime
  park_id      integer     [ref: > destinations_industrialpark.id, note: 'SET_NULL', null]
}

Table passes_accesspass {
  id             integer     [pk, increment]
  visitor_name   varchar(150)
  plate          varchar(20)
  pass_type      varchar(20) [note: '"single" | "day"']
  valid_from     datetime
  valid_to       datetime
  is_active      boolean     [default: true]
  is_used        boolean     [default: false]
  created_at     datetime
  updated_at     datetime

  created_by_id  integer     [ref: > users_user.id, note: 'CASCADE']
  destination_id integer     [ref: > destinations_destination.id, note: 'CASCADE']
}

Table access_accesslog {
  id              integer     [pk, increment]
  visitor_name    varchar(150)
  plate           varchar(20) [note: 'blank=True']
  notes           text        [note: 'blank=True']
  access_type     varchar(10) [note: '"qr" | "manual"']
  entry_time      datetime
  exit_time       datetime    [null]
  status          varchar(10) [note: '"open" | "closed"']
  created_at      datetime
  updated_at      datetime

  access_pass_id  integer     [ref: > passes_accesspass.id, note: 'SET_NULL', null]
  destination_id integer     [ref: > destinations_destination.id, note: 'CASCADE']
  guard_id        integer     [ref: > users_user.id, note: 'SET_NULL', null]
}
```
