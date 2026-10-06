FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d \
    && chmod +x /usr/sbin/policy-rc.d \
    && apt-get update \
    && apt-get install -y --no-install-recommends openssh-server iproute2 procps nano ca-certificates \
    && rm -rf /var/lib/apt/lists/* /etc/ssh/ssh_host_*

ARG NPA_USER=npa_ssh1
ENV NPA_USER=${NPA_USER}
RUN useradd --create-home --shell /bin/bash "${NPA_USER}" \
    && mkdir -p /run/sshd /etc/ssh/host_keys \
    && sed -i 's/session[[:space:]]*required[[:space:]]*pam_loginuid.so/session optional pam_loginuid.so/' /etc/pam.d/sshd

COPY sshd_config /etc/ssh/sshd_config
COPY entrypoint.sh /usr/local/bin/target-entrypoint
RUN chmod +x /usr/local/bin/target-entrypoint
EXPOSE 22
ENTRYPOINT ["/usr/local/bin/target-entrypoint"]
