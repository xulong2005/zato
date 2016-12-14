# -*- coding: utf-8 -*-

"""
Copyright (C) 2016, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

exeagent_conf = """
[bind]
host=0.0.0.0
port=39105

[crypto]
use_tls=True
tls_protocol=TLSv1
tls_ciphers=EECDH+AES:EDH+AES:-SHA1:EECDH+RC4:EDH+RC4:RC4-SHA:EECDH+AES256:EDH+AES256:AES256-SHA:!aNULL:!eNULL:!EXP:!LOW:!MD5
tls_client_certs=optional
priv_key_location=zato-exeagent-priv-key.pem
pub_key_location=zato-exeagent-pub-key.pem
cert_location=zato-exeagent-cert.pem
ca_certs_location=zato-exeagent-ca-certs.pem

[api_users]
user1=USER1_PASWORD
"""

logging_conf = """
loggers:
    '':
        level: INFO
        handlers: [stdout, default]
    zato:
        level: INFO
        handlers: [stdout, default]
        qualname: zato
        propagate: false
handlers:
    default:
        formatter: default
        class: logging.handlers.ConcurrentRotatingFileHandler
        filename: 'exeagent.log'
        mode: 'a'
        maxBytes: 20000000
        backupCount: 10
formatters:
    default:
        format: '%(asctime)s - %(levelname)s - %(process)d:%(threadName)s - %(name)s:%(lineno)d - %(message)s'
version: 1
"""
