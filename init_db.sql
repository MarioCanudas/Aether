-- Definición de tipos ENUM
CREATE TYPE transaction_type AS ENUM ('Abono', 'Cargo', 'Saldo inicial');
CREATE TYPE bank_name AS ENUM ('amex', 'banorte', 'bbva', 'banamex', 'hsbc', 'inbursa', 'nu', 'santander', 'cash');
CREATE TYPE statement_type_enum AS ENUM ('debit', 'credit');
create type category_group as enum ('Hogar', 'Transporte', 'Alimentacion', 'Ocio', 'Salud', 'Finanzas', 'Ingresos', 'Otros');
create type goal_type as enum ('Presupuesto', 'Ahorro', 'Deuda', 'Ingresos');
create type goal_status as enum ('Activo', 'Inactivo', 'Cumplido', 'Fallido');
create type template_type as enum ('transaction', 'goal');

---
-- Table: users
---
CREATE table if not exists "users" (
    "user_id" BIGSERIAL PRIMARY KEY,
    "username" VARCHAR(255) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255),
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "last_login" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE
);

---
-- Table: categories
---

CREATE table if not exists "categories" (
    "category_id" BIGSERIAL PRIMARY KEY,
    "user_id" bigint,
    "group" category_group not null,
    "name" varchar NOT NULL UNIQUE,
    "description" text
);

---
-- Table: transactions (Parent Table for Partitioning)
---
CREATE TABLE if not exists "transactions" (
    "transaction_id" BIGSERIAL,
    "user_id" BIGSERIAL NOT NULL,
    "date" DATE NOT NULL,
    "category_id" bigint,
    "card_id" bigint,
    "description" VARCHAR(500),
    "amount" DECIMAL(18, 2) NOT NULL,
    "type" transaction_type NOT NULL,
    "bank" bank_name NOT NULL,
    "statement_type" statement_type_enum NOT NULL,
    "filename" VARCHAR(255),
    PRIMARY KEY ("transaction_id", "date")
) PARTITION BY RANGE ("date");

-- Índices en la tabla padre para optimizar consultas que involucran todas las particiones o para el backend
-- CREATE INDEX idx_transactions_user_id_date ON transactions (user_id, date);
-- CREATE INDEX idx_transactions_date ON transactions (date);

---
-- Table: budgets
---

CREATE TABLE if not exists "goals" (
    "goal_id" BIGSERIAL PRIMARY KEY,
    "user_id" bigint NOT NULL,
    "category_id" bigint,
    "type" goal_type not null,
    "amount" decimal(18, 2) NOT NULL,
    "added_amount" decimal(18, 2) default 0,
    "name" varchar NOT NULL,
    "created_at" timestamp NOT null DEFAULT CURRENT_TIMESTAMP,
    "start_date" timestamp NOT NULL,
    "end_date" timestamp NOT null,
    "achieved" boolean,
    "status" goal_status default 'Activo'
);

---
-- Table: templates
---

create table if not exists "templates" (
	"template_id" BIGSERIAL primary key,
	"user_id" bigserial,
  "card_id" bigint,
    "template_name" varchar(50) NOT NULL,
    "template_description" varchar(200),
    "template_type" template_type not null,
    "default_values" json not null
);

create table if not exists "cards" (
    "card_id" bigserial primary key,
  "user_id" bigint,
  "name" varchar(50) NOT NULL,
  "bank" bank_name NOT NULL,
  "statement_type" statement_type_enum NOT NULL
);

---
-- Foreign Keys
---

-- transactions
alter table "transactions" add constraint "fk_transactions_user_id" foreign key("user_id") REFERENCES "users"("user_id") ON DELETE cascade;
alter table "transactions" add constraint "fk_transactions_category_id" FOREIGN KEY("category_id") REFERENCES "categories"("category_id");
alter table "transactions" add constraint "fk_cards_card_id_transactions_card_id" FOREIGN KEY("card_id") REFERENCES "cards"("card_id");

-- budgets
ALTER TABLE "goals" ADD CONSTRAINT "fk_goals_user_id" FOREIGN KEY("user_id") REFERENCES "users"("user_id") on delete cascade;
ALTER TABLE "goals" ADD CONSTRAINT "fk_goals_category_id" FOREIGN KEY("category_id") REFERENCES "categories"("category_id");

-- categories
ALTER TABLE "categories" ADD CONSTRAINT "fk_categories_user_id" FOREIGN KEY("user_id") REFERENCES "users"("user_id");
alter table "templates" add constraint "fk_cards_card_id_templates_card_id" foreign key("card_id") references "cards"("card_id");

-- templates
alter table "templates" add constraint "fk_templates_user_id_users_id" FOREIGN KEY("user_id") REFERENCES "users"("user_id");

-- cards
ALTER TABLE "cards" ADD CONSTRAINT "fk_cards_user_id_users_id" FOREIGN KEY("user_id") REFERENCES "users"("user_id");
