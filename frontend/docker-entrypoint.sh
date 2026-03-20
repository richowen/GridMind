#!/bin/sh
# GridMind frontend entrypoint.
# Generates /etc/nginx/auth.conf (included by nginx.conf) and /etc/nginx/.htpasswd
# from GRIDMIND_USER / GRIDMIND_PASS env vars, then starts nginx.
#
# Auth enabled:  set both GRIDMIND_USER and GRIDMIND_PASS
# Auth disabled: leave either variable unset or empty

set -e

HTPASSWD_FILE="/etc/nginx/.htpasswd"
AUTH_CONF="/etc/nginx/auth.conf"

if [ -n "${GRIDMIND_USER}" ] && [ -n "${GRIDMIND_PASS}" ]; then
    echo "GridMind: enabling basic auth for user '${GRIDMIND_USER}'"
    # Use -bi (batch + stdin) so the password is never visible in the process list.
    printf '%s' "${GRIDMIND_PASS}" | htpasswd -bi "${HTPASSWD_FILE}" "${GRIDMIND_USER}"
    # Write nginx snippet that enables auth
    cat > "${AUTH_CONF}" <<EOF
auth_basic           "GridMind";
auth_basic_user_file ${HTPASSWD_FILE};
EOF
    echo "GridMind: basic auth enabled"
else
    echo "GridMind: GRIDMIND_USER/GRIDMIND_PASS not set — basic auth disabled"
    # Write nginx snippet that disables auth
    cat > "${AUTH_CONF}" <<EOF
auth_basic off;
EOF
fi

exec nginx -g "daemon off;"
