FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive LANG=en_US.UTF-8
RUN printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d \
    && chmod +x /usr/sbin/policy-rc.d \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       xrdp xorgxrdp xserver-xorg-core xfce4 xfce4-terminal mousepad \
       dbus-x11 supervisor openssl locales fonts-dejavu-core procps \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system rdpusers \
    && useradd --create-home --shell /bin/bash --groups rdpusers npa_desktop \
    && usermod -a -G ssl-cert xrdp \
    && sed -i \
       -e 's/^security_layer=.*/security_layer=tls/' \
       -e 's|^certificate=.*|certificate=/etc/xrdp/cert.pem|' \
       -e 's|^key_file=.*|key_file=/etc/xrdp/key.pem|' \
       -e 's/^autorun=.*/autorun=Xorg/' /etc/xrdp/xrdp.ini \
    && sed -i \
       -e 's/^AllowRootLogin=.*/AllowRootLogin=false/' \
       -e 's/^TerminalServerUsers=.*/TerminalServerUsers=rdpusers/' \
       -e 's/^AlwaysGroupCheck=.*/AlwaysGroupCheck=true/' \
       -e 's/^EnableUserWindowManager=.*/EnableUserWindowManager=false/' \
       -e 's|^param=Xorg$|param=/usr/lib/xorg/Xorg|' /etc/xrdp/sesman.ini

COPY startwm.sh /etc/xrdp/startwm.sh
COPY xrdp-sesman.pam /etc/pam.d/xrdp-sesman
COPY supervisord.conf /etc/supervisor/conf.d/playground.conf
COPY entrypoint.sh /usr/local/bin/desktop-entrypoint
RUN chmod +x /etc/xrdp/startwm.sh /usr/local/bin/desktop-entrypoint
EXPOSE 3389
ENTRYPOINT ["/usr/local/bin/desktop-entrypoint"]
