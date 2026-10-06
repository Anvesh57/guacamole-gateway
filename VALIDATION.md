# Validation record

Prepared on 2026-09-27.

## Executed successfully

- Parsed `compose.yaml` and validated it against the official Compose specification JSON schema.
- Checked all shell scripts with `bash -n` and compiled both Python scripts.
- Imported the Guacamole schema, configuration and seed using Ubuntu 24.04's real OpenLDAP 2.6.7 `slaptest` and `slapadd` binaries.
- Ran an isolated OpenLDAP server on localhost with the project's schema, seed and ACLs. Only executable, schema, module, database and PID paths and the listen port were changed for this environment.
- Confirmed Bob and Alice can bind with their own passwords, and incorrect passwords fail.
- Confirmed there are exactly two human directory entries, two business access groups and three machine definitions.
- Queried the directory using the connection-filter structure from Guacamole 1.6.0's `ConnectionService`: Bob receives precisely the two SSH definitions; Alice receives precisely the desktop definition.
- Confirmed direct LDAP lookups cannot retrieve an unauthorized machine's connection parameters.
- Confirmed LDAP password attributes are unreadable to ordinary users, and Bob cannot add himself to another group.
- Added Bob to `Desktop users`: his connection query then returned all three machines. Removed that membership: it returned only the two SSH machines again. No connection objects were edited.
- Restarted the isolated LDAP process and confirmed identities and access rules persisted.
- Exercised the smoke-test protocol parser with fragmented messages and split UTF-8 input; checked malformed-length rejection.
- Checked password rendering with punctuation, spaces and non-ASCII characters; verified salted LDAP password hashes and rejection of newline injection.
- Confirmed connection entries contain no direct Bob/Alice grants or portal-credential passthrough tokens.

## Not executed here

Docker and a Docker daemon were unavailable in the authoring workspace. The container images were therefore not built or launched here, and the complete Guacamole web application, SSH sessions and XFCE/RDP sessions were not exercised together. Compose schema validation is not a substitute for `docker compose config` or a live deployment.

The LDAP test validates real directory behavior. It does not claim that a Guacamole JVM ran here. The included `tests/smoke.py` and `scripts/check-group-change.sh` were syntax/component checked but need the live Compose stack for their integration checks.

## Run on your Docker host

```bash
cp .env.example .env
docker compose config --quiet
docker compose up -d --build
docker compose --profile test run --rm verify
bash scripts/check-group-change.sh
```

Finish the README's browser checks, including `whoami; hostname` in all three target sessions. The automated tunnel checks verify display output, not the final visual state of the desktop.
