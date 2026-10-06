FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d \
    && chmod +x /usr/sbin/policy-rc.d \
    && echo 'slapd slapd/no_configuration boolean true' | debconf-set-selections \
    && apt-get update \
    && apt-get install -y --no-install-recommends slapd ldap-utils python3 \
    && rm -rf /var/lib/apt/lists/* /var/lib/ldap/*

COPY guacConfigGroup.schema /etc/ldap/schema/guacConfigGroup.schema
COPY slapd.conf.template /etc/ldap/slapd.conf.template
COPY seed.ldif.template render.py entrypoint.sh /opt/ldap/
RUN chmod +x /opt/ldap/entrypoint.sh
EXPOSE 389
ENTRYPOINT ["/opt/ldap/entrypoint.sh"]
