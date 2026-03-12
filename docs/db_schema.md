```dbml
// GateFlow — Database Schema
// https://dbdiagram.io

Table destinations_industrialpark {
  id          integer     [pk, increment]
  name        varchar(100)
  address     text        [note: 'blank=True']
  created_at  datetime
}

Table destinations_destination {
  id           integer     [pk, increment]
  name         varchar(100)
  type         varchar(10) [note: '"company" | "area"']
  contact_info text        [null]
  is_active    boolean     [default: true]
  park_id      integer     [ref: > destinations_industrialpark.id, note: 'SET_NULL', null]
}

Table destinations_visitreason {
  id        integer     [pk, increment]
  name      varchar(80)
  is_active boolean     [default: true]
}

Table users_user {
  id           integer     [pk, increment]
  email        varchar     [unique]
  username     varchar(150)[note: 'autogenerado desde email']
  role         varchar(20) [note: '"admin" | "guard" | "company"']
  is_active    boolean     [default: true]
  is_staff     boolean     [default: false]
  is_superuser boolean     [default: false]
  date_joined  datetime
  park_id      integer     [ref: > destinations_industrialpark.id, note: 'SET_NULL', null]
}

// Tabla intermedia del M2M User.destinations
Table users_user_destinations {
  id             integer [pk, increment]
  user_id        integer [ref: > users_user.id]
  destination_id integer [ref: > destinations_destination.id]

  indexes {
    (user_id, destination_id) [unique]
  }
}

Table passes_accesspass {
  id             integer     [pk, increment]
  visitor_name   varchar(100)
  plate          varchar(20)
  pass_type      varchar(20) [note: '"single_use" | "day_pass"']
  valid_from     date
  valid_until    date
  qr_code        text        [unique, note: 'generado por el servidor']
  is_used        boolean     [default: false]
  created_at     datetime

  // FK al usuario company que generó el pase
  company_id     integer     [ref: > users_user.id, note: 'SET_NULL', null]

  // FK al destino específico elegido al generar el pase
  // (debe ser uno de los destinos del M2M del company)
  destination_id integer     [ref: > destinations_destination.id, note: 'SET_NULL', null]

  // FK al motivo de visita
  reason_id      integer     [ref: > destinations_visitreason.id, note: 'SET_NULL', null]
}

Table access_accesslog {
  id           integer     [pk, increment]
  visitor_name varchar(100)
  plate        varchar(20)
  access_type  varchar(10) [note: '"manual" | "qr"']
  entry_time   datetime
  exit_time    datetime    [null]

  // FK al pase que originó esta entrada (null si access_type = manual)
  pass_id        integer   [ref: > passes_accesspass.id, note: 'SET_NULL', null]

  // FK al destino (desnormalizado para consultas rápidas sin pasar por el pase)
  destination_id integer   [ref: > destinations_destination.id, note: 'SET_NULL', null]

  // FK al motivo (igual, desnormalizado)
  reason_id      integer   [ref: > destinations_visitreason.id, note: 'SET_NULL', null]

  // Guardia que registró el acceso
  guard_id       integer   [ref: > users_user.id, note: 'SET_NULL', null]
}
```
