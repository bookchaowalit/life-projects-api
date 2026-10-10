-- Roles for the projects database. Locally a superuser runs this; on Neon
-- `projects-db provision` creates the same roles through the migrator.
--
-- projects_migrator  owns the schema and runs migrations only.
-- projects_api       the API at runtime: no superuser, no BYPASSRLS, owns nothing.
-- projects_publisher sweeps and marks the outbox across workspaces; nothing else.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'projects_migrator') THEN
        CREATE ROLE projects_migrator LOGIN NOSUPERUSER NOCREATEROLE NOBYPASSRLS;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'projects_api') THEN
        CREATE ROLE projects_api LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'projects_publisher') THEN
        CREATE ROLE projects_publisher LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
END
$$;
