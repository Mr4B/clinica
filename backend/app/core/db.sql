CREATE TABLE "structures" (
    "id" SERIAL,
    "name" varchar(100) NOT NULL UNIQUE,
    "location" varchar(255),
    CONSTRAINT "pk_table_6_id" PRIMARY KEY ("id")
);

CREATE TABLE "users" (
    "id" uuid NOT NULL,
    "first_name" varchar(100),
    "last_name" varchar(100),
    "username" varchar(100) NOT NULL UNIQUE,
    "hashed_password" text NOT NULL,
    "structure_id" integer,
    "role_id" integer,
    "is_superuser" boolean DEFAULT False,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "pk_users_id" PRIMARY KEY ("id")
);

-- La tabella che contiene il catalogo di tutti i moduli disponibili
-- 
CREATE TABLE "module_catalog" (
    "module_id" SERIAL,
    "code" varchar(10) NOT NULL UNIQUE,
    "name" varchar(100),
    -- Praticamente descrive la versione da utilizzare del modulo (prevedendo aggiornamenti delle schede)
    "current_schema_version" integer NOT NULL,
    "active" boolean NOT NULL DEFAULT True,
    "updated_at" date,
    CONSTRAINT "pk_table_6_id" PRIMARY KEY ("module_id")
);
COMMENT ON TABLE "module_catalog" IS 'La tabella che contiene il catalogo di tutti i moduli disponibili';
COMMENT ON COLUMN "module_catalog"."current_schema_version" IS 'Praticamente descrive la versione da utilizzare del modulo (prevedendo aggiornamenti delle schede)';
-- Indexes
CREATE UNIQUE INDEX "module_catalog_module_code" ON "module_catalog" ("code");

CREATE TABLE "roles" (
    "id" SERIAL,
    "name" varchar(100) NOT NULL,
    "modules" json,
    "created_by" uuid NOT NULL,
    CONSTRAINT "pk_table_6_id" PRIMARY KEY ("id")
);

-- sarebbe la scheda 0.2
CREATE TABLE "dossiers" (
    "dossier_id" integer NOT NULL,
    -- data di ricovero
    "admission_date" date,
    -- data di dimissione
    -- 
    "discharge_date" date,
    "patient_id" uuid,
    "structure_id" integer,
    "created_by" uuid,
    "created_at" timestamp,
    CONSTRAINT "pk_table_7_id" PRIMARY KEY ("dossier_id")
);
COMMENT ON TABLE "dossiers" IS 'sarebbe la scheda 0.2';
COMMENT ON COLUMN "dossiers"."admission_date" IS 'data di ricovero';
COMMENT ON COLUMN "dossiers"."discharge_date" IS 'data di dimissione';

CREATE TABLE "module_entries" (
    "entry_id" uuid NOT NULL,
    "dossier_id" integer NOT NULL,
    "module_code" varchar(10) NOT NULL,
    "schema_version" integer NOT NULL,
    "data" jsonb NOT NULL,
    "created_by" uuid NOT NULL,
    "created_at" timestamp NOT NULL,
    CONSTRAINT "pk_table_7_id" PRIMARY KEY ("entry_id")
);

CREATE TABLE "audit_log" (
    "audit_id" integer NOT NULL,
    "ts" timestamp,
    "user_id" uuid,
    "username" varchar(255),
    -- READ/CREATE/UPDATE/DELETE
    "action" varchar(20),
    "table_name" varchar(100),
    "record_id" varchar(50),
    "brefore" jsonb,
    "after" jsonb,
    CONSTRAINT "pk_table_8_id" PRIMARY KEY ("audit_id")
);
COMMENT ON COLUMN "audit_log"."action" IS 'READ/CREATE/UPDATE/DELETE';

CREATE TABLE "patients" (
    "patient_id" uuid NOT NULL,
    -- Codice interno suggerito da chat, non so precisamente il suo utilizzo
    -- 
    "code" integer UNIQUE,
    "first_name" varchar(100),
    "last_name" varchar(100),
    -- sensibile
    -- 
    "date_of_birth" date,
    -- sensibile
    -- 
    "tax_code" varchar,
    "created_at" timestamp DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "pk_table_6_id" PRIMARY KEY ("patient_id")
);
COMMENT ON COLUMN "patients"."code" IS 'Codice interno suggerito da chat, non so precisamente il suo utilizzo';
COMMENT ON COLUMN "patients"."date_of_birth" IS 'sensibile';
COMMENT ON COLUMN "patients"."tax_code" IS 'sensibile';

-- Foreign key constraints
-- Schema: public
ALTER TABLE "module_entries" ADD CONSTRAINT "fk_module_entries_dossier_id_dossiers_dossier_id" FOREIGN KEY("dossier_id") REFERENCES "dossiers"("dossier_id");
ALTER TABLE "module_catalog" ADD CONSTRAINT "fk_module_catalog_code_module_entries_module_code" FOREIGN KEY("code") REFERENCES "module_entries"("module_code");
ALTER TABLE "dossiers" ADD CONSTRAINT "fk_dossiers_patient_id_patients_patient_id" FOREIGN KEY("patient_id") REFERENCES "patients"("patient_id");
ALTER TABLE "users" ADD CONSTRAINT "fk_users_role_id_roles_id" FOREIGN KEY("role_id") REFERENCES "roles"("id");
ALTER TABLE "users" ADD CONSTRAINT "fk_users_structure_id_structures_id" FOREIGN KEY("structure_id") REFERENCES "structures"("id");
ALTER TABLE "dossiers" ADD CONSTRAINT "fk_dossiers_structure_id_structures_id" FOREIGN KEY("structure_id") REFERENCES "structures"("id");
ALTER TABLE "roles" ADD CONSTRAINT "fk_roles_created_by_users_id" FOREIGN KEY("created_by") REFERENCES "users"("id");
ALTER TABLE "dossiers" ADD CONSTRAINT "fk_dossiers_created_by_users_id" FOREIGN KEY("created_by") REFERENCES "users"("id");
ALTER TABLE "module_entries" ADD CONSTRAINT "fk_module_entries_created_by_users_id" FOREIGN KEY("created_by") REFERENCES "users"("id");
ALTER TABLE "audit_log" ADD CONSTRAINT "fk_audit_log_user_id_users_id" FOREIGN KEY("user_id") REFERENCES "users"("id");