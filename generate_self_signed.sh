#!/bin/bash

grep "^extendedKeyUsage = serverAuth" /etc/pki/tls/openssl.cnf > /dev/null
if [ $? -ne 0 ]; then

sed -i '/^keyUsage = .*/a extendedKeyUsage = serverAuth,clientAuth' /etc/pki/tls/openssl.cnf

/usr/bin/openssl genrsa -rand /proc/apm:/proc/cpuinfo:/proc/dma:/proc/filesystems:/proc/interrupts:/proc/ioports:/proc/pci:/proc/rtc:/proc/uptime 2048 > /etc/pki/tls/private/localhost.key 2> /dev/null

FQDN=`hostname`
if [ "x${FQDN}" = "x" -o ${#FQDN} -gt 59 ]; then
   FQDN=localhost.localdomain
fi

cat << EOF | /usr/bin/openssl req -new -key /etc/pki/tls/private/localhost.key \
         -x509 -sha256 -days 365 -set_serial $RANDOM -extensions v3_req \
         -out /etc/pki/tls/certs/localhost.crt 2>/dev/null
--
SomeState
SomeCity
Issabel
PBX
${FQDN}
root@${FQDN}
EOF

# To check certificate from CLI
# openssl x509 -text -noout -in /etc/pki/tls/certs/localhost.crt

/usr/bin/systemctl restart httpd > /dev/null 2>&1

fi
