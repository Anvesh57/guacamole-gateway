#!/bin/bash
# Temporarily grant Bob Desktop access by changing LDAP membership only.
set -euo pipefail
cd "$(dirname "$0")/.."

verify() {
    docker compose --profile test run --rm --no-deps verify --matrix-only "$@"
}

modify() {
    docker compose exec -T ldap sh -c \
        'ldapmodify -x -H ldap://127.0.0.1:389 -D "cn=admin,dc=example,dc=org" -w "$LDAP_ADMIN_PASSWORD"'
}

# Require the initial matrix before changing anything.
verify
changed=false
cleanup() {
    if [[ "$changed" == true ]]; then
        modify <<'LDIF'
dn: cn=Desktop users,ou=groups,dc=example,dc=org
changetype: modify
delete: member
member: uid=bob,ou=people,dc=example,dc=org

LDIF
        changed=false
    fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

modify <<'LDIF'
dn: cn=Desktop users,ou=groups,dc=example,dc=org
changetype: modify
add: member
member: uid=bob,ou=people,dc=example,dc=org

LDIF
changed=true

# A fresh login should now expose all three machines to Bob.
verify --bob-extra-desktop
cleanup
trap - EXIT
# A fresh login should restore the original two-machine view.
verify
echo 'PASS: adding/removing only LDAP group membership grants/revokes access.'
