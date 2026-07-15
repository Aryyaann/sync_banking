-- Esquema de la base de datos - sync_banking
CREATE TABLE businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE bank_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    bank_name TEXT NOT NULL,
    application_id TEXT NOT NULL,
    account_uid TEXT NOT NULL,
    session_id TEXT NOT NULL,
    consent_valid_until TIMESTAMPTZ NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE categorization_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('iban_importe', 'iban', 'texto_contiene')),
    criterio TEXT NOT NULL,
    concepto_detallado TEXT NOT NULL,
    categoria TEXT,
    notas TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    bank_connection_id UUID NOT NULL REFERENCES bank_connections(id) ON DELETE CASCADE,
    referencia_unica TEXT NOT NULL,
    fecha DATE NOT NULL,
    importe NUMERIC(12,2) NOT NULL,
    moneda TEXT NOT NULL DEFAULT 'EUR',
    tipo TEXT NOT NULL CHECK (tipo IN ('Entrada', 'Salida')),
    contraparte TEXT,
    iban_contraparte TEXT,
    concepto_banco TEXT,
    concepto_detallado TEXT,
    categoria TEXT,
    referencia TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (business_id, referencia_unica)
);

CREATE INDEX idx_transactions_business ON transactions(business_id);
CREATE INDEX idx_transactions_fecha ON transactions(fecha);
