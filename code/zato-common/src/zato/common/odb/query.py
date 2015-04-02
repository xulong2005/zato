# -*- coding: utf-8 -*-

"""
Copyright (C) 2011 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import logging
from functools import wraps

# SQLAlchemy
from sqlalchemy import func, not_
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import case

# Zato
from zato.common import DEFAULT_HTTP_PING_METHOD, DEFAULT_HTTP_POOL_SIZE, HTTP_SOAP_SERIALIZATION_TYPE, PARAMS_PRIORITY, \
     URL_PARAMS_PRIORITY
from zato.common.odb import model as m

logger = logging.getLogger(__name__)

def needs_columns(func):
    """ A decorator for queries which works out whether a given query function
    should return the result only or a column list retrieved in addition
    to the result. This is useful because some callers prefer the former and
    some need the latter.
    """
    @wraps(func)
    def inner(*args):
        # needs_columns is always the last argument so we don't have to look
        # it up using the 'inspect' module or anything like that.
        needs_columns = args[-1]

        q = func(*args)

        if needs_columns:
            return q.all(), q.statement.columns
        return q.all()

    return inner

# ################################################################################################################################

def internal_channel_list(session, cluster_id):
    """ All the HTTP/SOAP channels that point to internal services.
    """
    return session.query(
        m.HTTPSOAP.soap_action, m.Service.name).\
        filter(m.HTTPSOAP.cluster_id==m.Cluster.id).\
        filter(m.HTTPSOAP.service_id==m.Service.id).filter(m.Service.is_internal==True).filter(m.Cluster.id==cluster_id).filter(m.Cluster.id==m.HTTPSOAP.cluster_id) # noqa

# ################################################################################################################################

def _job(session, cluster_id):
    return session.query(
        m.Job.id, m.Job.name, m.Job.is_active,
        m.Job.job_type, m.Job.start_date, m.Job.extra,
        m.Service.name.label('service_name'), m.Service.impl_name.label('service_impl_name'),
        m.Service.id.label('service_id'),
        m.IntervalBasedJob.weeks, m.IntervalBasedJob.days,
        m.IntervalBasedJob.hours, m.IntervalBasedJob.minutes,
        m.IntervalBasedJob.seconds, m.IntervalBasedJob.repeats,
        m.CronStyleJob.cron_definition).\
        outerjoin(m.IntervalBasedJob, m.Job.id==m.IntervalBasedJob.job_id).\
        outerjoin(m.CronStyleJob, m.Job.id==m.CronStyleJob.job_id).\
        filter(m.Job.cluster_id==m.Cluster.id).\
        filter(m.Job.service_id==m.Service.id).\
        filter(m.Cluster.id==cluster_id).\
        order_by('job.name')

@needs_columns
def job_list(session, cluster_id, needs_columns=False):
    """ All the scheduler's jobs defined in the ODB.
    """
    return _job(session, cluster_id)

def job_by_name(session, cluster_id, name):
    """ A scheduler's job fetched by its name.
    """
    return _job(session, cluster_id).\
        filter(m.Job.name==name).\
        one()

# ################################################################################################################################

@needs_columns
def apikey_security_list(session, cluster_id, needs_columns=False):
    """ All the API keys.
    """
    return session.query(
        m.APIKeySecurity.id, m.APIKeySecurity.name,
        m.APIKeySecurity.is_active,
        m.APIKeySecurity.username,
        m.APIKeySecurity.password, m.APIKeySecurity.sec_type).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.APIKeySecurity.cluster_id).\
        filter(m.SecurityBase.id==m.APIKeySecurity.id).\
        order_by('sec_base.name')

@needs_columns
def aws_security_list(session, cluster_id, needs_columns=False):
    """ All the Amazon security definitions.
    """
    return session.query(
        m.AWSSecurity.id, m.AWSSecurity.name,
        m.AWSSecurity.is_active,
        m.AWSSecurity.username,
        m.AWSSecurity.password, m.AWSSecurity.sec_type).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.AWSSecurity.cluster_id).\
        filter(m.SecurityBase.id==m.AWSSecurity.id).\
        order_by('sec_base.name')

@needs_columns
def basic_auth_list(session, cluster_id, needs_columns=False):
    """ All the HTTP Basic Auth definitions.
    """
    return session.query(
        m.HTTPBasicAuth.id, m.HTTPBasicAuth.name,
        m.HTTPBasicAuth.is_active,
        m.HTTPBasicAuth.username, m.HTTPBasicAuth.realm,
        m.HTTPBasicAuth.password, m.HTTPBasicAuth.sec_type,
        m.HTTPBasicAuth.password_type).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.HTTPBasicAuth.cluster_id).\
        filter(m.SecurityBase.id==m.HTTPBasicAuth.id).\
        order_by('sec_base.name')

@needs_columns
def ntlm_list(session, cluster_id, needs_columns=False):
    """ All the m.NTLM definitions.
    """
    return session.query(
        m.NTLM.id, m.NTLM.name,
        m.NTLM.is_active,
        m.NTLM.username,
        m.NTLM.password, m.NTLM.sec_type,
        m.NTLM.password_type).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.NTLM.cluster_id).\
        filter(m.SecurityBase.id==m.NTLM.id).\
        order_by('sec_base.name')

@needs_columns
def oauth_list(session, cluster_id, needs_columns=False):
    """ All the m.OAuth definitions.
    """
    return session.query(
        m.OAuth.id, m.OAuth.name,
        m.OAuth.is_active,
        m.OAuth.username, m.OAuth.password,
        m.OAuth.proto_version, m.OAuth.sig_method,
        m.OAuth.max_nonce_log, m.OAuth.sec_type).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.OAuth.cluster_id).\
        filter(m.SecurityBase.id==m.OAuth.id).\
        order_by('sec_base.name')

@needs_columns
def openstack_security_list(session, cluster_id, needs_columns=False):
    """ All the m.OpenStackSecurity definitions.
    """
    return session.query(
        m.OpenStackSecurity.id, m.OpenStackSecurity.name, m.OpenStackSecurity.is_active,
        m.OpenStackSecurity.username, m.OpenStackSecurity.sec_type).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.OpenStackSecurity.cluster_id).\
        filter(m.SecurityBase.id==m.OpenStackSecurity.id).\
        order_by('sec_base.name')

@needs_columns
def tech_acc_list(session, cluster_id, needs_columns=False):
    """ All the technical accounts.
    """
    return session.query(
        m.TechnicalAccount.id, m.TechnicalAccount.name,
        m.TechnicalAccount.is_active,
        m.TechnicalAccount.password, m.TechnicalAccount.salt,
        m.TechnicalAccount.sec_type, m.TechnicalAccount.password_type).\
        order_by(m.TechnicalAccount.name).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.TechnicalAccount.cluster_id).\
        filter(m.SecurityBase.id==m.TechnicalAccount.id).\
        order_by('sec_base.name')

@needs_columns
def tls_ca_cert_list(session, cluster_id, needs_columns=False):
    """ TLS CA certs.
    """
    return session.query(m.TLSCACert).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.TLSCACert.cluster_id).\
        order_by('sec_tls_ca_cert.name')

@needs_columns
def tls_channel_sec_list(session, cluster_id, needs_columns=False):
    """ TLS-based channel security.
    """
    return session.query(
        m.TLSChannelSecurity.id, m.TLSChannelSecurity.name,
        m.TLSChannelSecurity.is_active, m.TLSChannelSecurity.value,
        m.TLSChannelSecurity.sec_type).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.TLSChannelSecurity.cluster_id).\
        filter(m.SecurityBase.id==m.TLSChannelSecurity.id).\
        order_by('sec_base.name')

@needs_columns
def tls_key_cert_list(session, cluster_id, needs_columns=False):
    """ TLS key/cert pairs.
    """
    return session.query(
        m.TLSKeyCertSecurity.id, m.TLSKeyCertSecurity.name,
        m.TLSKeyCertSecurity.is_active, m.TLSKeyCertSecurity.info,
        m.TLSKeyCertSecurity.value, m.TLSKeyCertSecurity.sec_type).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.TLSKeyCertSecurity.cluster_id).\
        filter(m.SecurityBase.id==m.TLSKeyCertSecurity.id).\
        order_by('sec_base.name')

@needs_columns
def wss_list(session, cluster_id, needs_columns=False):
    """ All the WS-Security definitions.
    """
    return session.query(
        m.WSSDefinition.id, m.WSSDefinition.name, m.WSSDefinition.is_active,
        m.WSSDefinition.username, m.WSSDefinition.password, m.WSSDefinition.password_type,
        m.WSSDefinition.reject_empty_nonce_creat, m.WSSDefinition.reject_stale_tokens,
        m.WSSDefinition.reject_expiry_limit, m.WSSDefinition.nonce_freshness_time,
        m.WSSDefinition.sec_type).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.WSSDefinition.cluster_id).\
        filter(m.SecurityBase.id==m.WSSDefinition.id).\
        order_by('sec_base.name')

@needs_columns
def xpath_sec_list(session, cluster_id, needs_columns=False):
    """ All the m.XPath security definitions.
    """
    return session.query(
        m.XPathSecurity.id, m.XPathSecurity.name, m.XPathSecurity.is_active, m.XPathSecurity.username, m.XPathSecurity.username_expr,
        m.XPathSecurity.password_expr, m.XPathSecurity.password, m.XPathSecurity.sec_type).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.XPathSecurity.cluster_id).\
        filter(m.SecurityBase.id==m.XPathSecurity.id).\
        order_by('sec_base.name')

# ################################################################################################################################

def _def_amqp(session, cluster_id):
    return session.query(
        m.ConnDefAMQP.name, m.ConnDefAMQP.id, m.ConnDefAMQP.host,
        m.ConnDefAMQP.port, m.ConnDefAMQP.vhost, m.ConnDefAMQP.username,
        m.ConnDefAMQP.frame_max, m.ConnDefAMQP.heartbeat, m.ConnDefAMQP.password).\
        filter(m.ConnDefAMQP.def_type=='amqp').\
        filter(m.Cluster.id==m.ConnDefAMQP.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.ConnDefAMQP.name)

def def_amqp(session, cluster_id, id):
    """ A particular AMQP definition
    """
    return _def_amqp(session, cluster_id).\
        filter(m.ConnDefAMQP.id==id).\
        one()

@needs_columns
def def_amqp_list(session, cluster_id, needs_columns=False):
    """ AMQP connection definitions.
    """
    return _def_amqp(session, cluster_id)

# ################################################################################################################################

def _def_jms_wmq(session, cluster_id):
    return session.query(
        m.ConnDefWMQ.id, m.ConnDefWMQ.name, m.ConnDefWMQ.host,
        m.ConnDefWMQ.port, m.ConnDefWMQ.queue_manager, m.ConnDefWMQ.channel,
        m.ConnDefWMQ.cache_open_send_queues, m.ConnDefWMQ.cache_open_receive_queues,
        m.ConnDefWMQ.use_shared_connections, m.ConnDefWMQ.ssl, m.ConnDefWMQ.ssl_cipher_spec,
        m.ConnDefWMQ.ssl_key_repository, m.ConnDefWMQ.needs_mcd, m.ConnDefWMQ.max_chars_printed).\
        filter(m.Cluster.id==m.ConnDefWMQ.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.ConnDefWMQ.name)

def def_jms_wmq(session, cluster_id, id):
    """ A particular JMS WebSphere MQ definition
    """
    return _def_jms_wmq(session, cluster_id).\
        filter(m.ConnDefWMQ.id==id).\
        one()

@needs_columns
def def_jms_wmq_list(session, cluster_id, needs_columns=False):
    """ JMS WebSphere MQ connection definitions.
    """
    return _def_jms_wmq(session, cluster_id)

# ################################################################################################################################

def _out_amqp(session, cluster_id):
    return session.query(
        m.OutgoingAMQP.id, m.OutgoingAMQP.name, m.OutgoingAMQP.is_active,
        m.OutgoingAMQP.delivery_mode, m.OutgoingAMQP.priority, m.OutgoingAMQP.content_type,
        m.OutgoingAMQP.content_encoding, m.OutgoingAMQP.expiration, m.OutgoingAMQP.user_id,
        m.OutgoingAMQP.app_id, m.ConnDefAMQP.name.label('def_name'), m.OutgoingAMQP.def_id).\
        filter(m.OutgoingAMQP.def_id==m.ConnDefAMQP.id).\
        filter(m.ConnDefAMQP.id==m.OutgoingAMQP.def_id).\
        filter(m.Cluster.id==m.ConnDefAMQP.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.OutgoingAMQP.name)

def out_amqp(session, cluster_id, id):
    """ An outgoing AMQP connection.
    """
    return _out_amqp(session, cluster_id).\
        filter(m.OutgoingAMQP.id==id).\
        one()

@needs_columns
def out_amqp_list(session, cluster_id, needs_columns=False):
    """ Outgoing AMQP connections.
    """
    return _out_amqp(session, cluster_id)

# ################################################################################################################################

def _out_jms_wmq(session, cluster_id):
    return session.query(
        m.OutgoingWMQ.id, m.OutgoingWMQ.name, m.OutgoingWMQ.is_active,
        m.OutgoingWMQ.delivery_mode, m.OutgoingWMQ.priority, m.OutgoingWMQ.expiration,
        m.ConnDefWMQ.name.label('def_name'), m.OutgoingWMQ.def_id).\
        filter(m.OutgoingWMQ.def_id==m.ConnDefWMQ.id).\
        filter(m.ConnDefWMQ.id==m.OutgoingWMQ.def_id).\
        filter(m.Cluster.id==m.ConnDefWMQ.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.OutgoingWMQ.name)

def out_jms_wmq(session, cluster_id, id):
    """ An outgoing JMS WebSphere MQ connection (by ID).
    """
    return _out_jms_wmq(session, cluster_id).\
        filter(m.OutgoingWMQ.id==id).\
        one()

def out_jms_wmq_by_name(session, cluster_id, name):
    """ An outgoing JMS WebSphere MQ connection (by name).
    """
    return _out_jms_wmq(session, cluster_id).\
        filter(m.OutgoingWMQ.name==name).\
        first()

@needs_columns
def out_jms_wmq_list(session, cluster_id, needs_columns=False):
    """ Outgoing JMS WebSphere MQ connections.
    """
    return _out_jms_wmq(session, cluster_id)

# ################################################################################################################################

def _channel_amqp(session, cluster_id):
    return session.query(
        m.ChannelAMQP.id, m.ChannelAMQP.name, m.ChannelAMQP.is_active,
        m.ChannelAMQP.queue, m.ChannelAMQP.consumer_tag_prefix,
        m.ConnDefAMQP.name.label('def_name'), m.ChannelAMQP.def_id,
        m.ChannelAMQP.data_format,
        m.Service.name.label('service_name'),
        m.Service.impl_name.label('service_impl_name')).\
        filter(m.ChannelAMQP.def_id==m.ConnDefAMQP.id).\
        filter(m.ChannelAMQP.service_id==m.Service.id).\
        filter(m.Cluster.id==m.ConnDefAMQP.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.ChannelAMQP.name)

def channel_amqp(session, cluster_id, id):
    """ A particular AMQP channel.
    """
    return _channel_amqp(session, cluster_id).\
        filter(m.ChannelAMQP.id==id).\
        one()

@needs_columns
def channel_amqp_list(session, cluster_id, needs_columns=False):
    """ AMQP channels.
    """
    return _channel_amqp(session, cluster_id)

# ################################################################################################################################

def _channel_jms_wmq(session, cluster_id):
    return session.query(
        m.ChannelWMQ.id, m.ChannelWMQ.name, m.ChannelWMQ.is_active,
        m.ChannelWMQ.queue, m.ConnDefWMQ.name.label('def_name'), m.ChannelWMQ.def_id,
        m.ChannelWMQ.data_format, m.Service.name.label('service_name'),
        m.Service.impl_name.label('service_impl_name')).\
        filter(m.ChannelWMQ.def_id==m.ConnDefWMQ.id).\
        filter(m.ChannelWMQ.service_id==m.Service.id).\
        filter(m.Cluster.id==m.ConnDefWMQ.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.ChannelWMQ.name)

def channel_jms_wmq(session, cluster_id, id):
    """ A particular JMS WebSphere MQ channel.
    """
    return _channel_jms_wmq(session, cluster_id).\
        filter(m.ChannelWMQ.id==id).\
        one()

@needs_columns
def channel_jms_wmq_list(session, cluster_id, needs_columns=False):
    """ JMS WebSphere MQ channels.
    """
    return _channel_jms_wmq(session, cluster_id)

# ################################################################################################################################

def _out_zmq(session, cluster_id):
    return session.query(
        m.OutgoingZMQ.id, m.OutgoingZMQ.name, m.OutgoingZMQ.is_active,
        m.OutgoingZMQ.address, m.OutgoingZMQ.socket_type).\
        filter(m.Cluster.id==m.OutgoingZMQ.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.OutgoingZMQ.name)

def out_zmq(session, cluster_id, id):
    """ An outgoing ZeroMQ connection.
    """
    return _out_zmq(session, cluster_id).\
        filter(m.OutgoingZMQ.id==id).\
        one()

@needs_columns
def out_zmq_list(session, cluster_id, needs_columns=False):
    """ Outgoing ZeroMQ connections.
    """
    return _out_zmq(session, cluster_id)

# ################################################################################################################################

def _channel_zmq(session, cluster_id):
    return session.query(
        m.ChannelZMQ.id, m.ChannelZMQ.name, m.ChannelZMQ.is_active,
        m.ChannelZMQ.address, m.ChannelZMQ.socket_type, m.ChannelZMQ.sub_key, m.ChannelZMQ.data_format,
        m.Service.name.label('service_name'), m.Service.impl_name.label('service_impl_name')).\
        filter(m.Service.id==m.ChannelZMQ.service_id).\
        filter(m.Cluster.id==m.ChannelZMQ.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.ChannelZMQ.name)

def channel_zmq(session, cluster_id, id):
    """ An incoming ZeroMQ connection.
    """
    return _channel_zmq(session, cluster_id).\
        filter(m.ChannelZMQ.id==id).\
        one()

@needs_columns
def channel_zmq_list(session, cluster_id, needs_columns=False):
    """ Incoming ZeroMQ connections.
    """
    return _channel_zmq(session, cluster_id)

# ################################################################################################################################

def _http_soap(session, cluster_id):
    return session.query(
        m.HTTPSOAP.id, m.HTTPSOAP.name, m.HTTPSOAP.is_active,
        m.HTTPSOAP.is_internal, m.HTTPSOAP.transport, m.HTTPSOAP.host,
        m.HTTPSOAP.url_path, m.HTTPSOAP.method, m.HTTPSOAP.soap_action,
        m.HTTPSOAP.soap_version, m.HTTPSOAP.data_format, m.HTTPSOAP.security_id,
        m.HTTPSOAP.has_rbac,
        m.HTTPSOAP.connection, m.HTTPSOAP.content_type,
        case([(m.HTTPSOAP.ping_method != None, m.HTTPSOAP.ping_method)], else_=DEFAULT_HTTP_PING_METHOD).label('ping_method'), # noqa
        case([(m.HTTPSOAP.pool_size != None, m.HTTPSOAP.pool_size)], else_=DEFAULT_HTTP_POOL_SIZE).label('pool_size'),
        case([(m.HTTPSOAP.merge_url_params_req != None, m.HTTPSOAP.merge_url_params_req)], else_=True).label('merge_url_params_req'),
        case([(m.HTTPSOAP.url_params_pri != None, m.HTTPSOAP.url_params_pri)], else_=URL_PARAMS_PRIORITY.DEFAULT).label('url_params_pri'),
        case([(m.HTTPSOAP.params_pri != None, m.HTTPSOAP.params_pri)], else_=PARAMS_PRIORITY.DEFAULT).label('params_pri'),
        case([(
            m.HTTPSOAP.serialization_type != None, m.HTTPSOAP.serialization_type)], 
             else_=HTTP_SOAP_SERIALIZATION_TYPE.DEFAULT.id).label('serialization_type'),
        m.HTTPSOAP.audit_enabled,
        m.HTTPSOAP.audit_back_log,
        m.HTTPSOAP.audit_max_payload,
        m.HTTPSOAP.audit_repl_patt_type,
        m.HTTPSOAP.timeout,
        m.HTTPSOAP.sec_tls_ca_cert_id,
        m.TLSCACert.name.label('sec_tls_ca_cert_name'),
        m.SecurityBase.sec_type,
        m.Service.name.label('service_name'),
        m.Service.id.label('service_id'),
        m.Service.impl_name.label('service_impl_name'),
        m.SecurityBase.name.label('security_name'),
        m.SecurityBase.username.label('username'),
        m.SecurityBase.password.label('password'),
        m.SecurityBase.password_type.label('password_type'),).\
        outerjoin(m.Service, m.Service.id==m.HTTPSOAP.service_id).\
        outerjoin(m.TLSCACert, m.TLSCACert.id==m.HTTPSOAP.sec_tls_ca_cert_id).\
        outerjoin(m.SecurityBase, m.HTTPSOAP.security_id==m.SecurityBase.id).\
        filter(m.Cluster.id==m.HTTPSOAP.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.HTTPSOAP.name)

def http_soap_security_list(session, cluster_id, connection=None):
    """ HTTP/SOAP security definitions.
    """
    q = _http_soap(session, cluster_id)

    if connection:
        q = q.filter(m.HTTPSOAP.connection==connection)

    return q

def http_soap(session, cluster_id, id):
    """ An HTTP/SOAP connection.
    """
    return _http_soap(session, cluster_id).\
        filter(m.HTTPSOAP.id==id).\
        one()

@needs_columns
def http_soap_list(session, cluster_id, connection=None, transport=None, return_internal=True, needs_columns=False):
    """ HTTP/SOAP connections, both channels and outgoing ones.
    """
    q = _http_soap(session, cluster_id)

    if connection:
        q = q.filter(m.HTTPSOAP.connection==connection)

    if transport:
        q = q.filter(m.HTTPSOAP.transport==transport)

    if not return_internal:
        q = q.filter(not_(m.HTTPSOAP.name.startswith('zato')))

    return q

# ################################################################################################################################

def _out_sql(session, cluster_id):
    return session.query(m.SQLConnectionPool).\
        filter(m.Cluster.id==m.SQLConnectionPool.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.SQLConnectionPool.name)

def out_sql(session, cluster_id, id):
    """ An outgoing SQL connection.
    """
    return _out_sql(session, cluster_id).\
        filter(m.SQLConnectionPool.id==id).\
        one()

@needs_columns
def out_sql_list(session, cluster_id, needs_columns=False):
    """ Outgoing SQL connections.
    """
    return _out_sql(session, cluster_id)

# ################################################################################################################################

def _out_ftp(session, cluster_id):
    return session.query(
        m.OutgoingFTP.id, m.OutgoingFTP.name, m.OutgoingFTP.is_active,
        m.OutgoingFTP.host, m.OutgoingFTP.port, m.OutgoingFTP.user, m.OutgoingFTP.password,
        m.OutgoingFTP.acct, m.OutgoingFTP.timeout, m.OutgoingFTP.dircache).\
        filter(m.Cluster.id==m.OutgoingFTP.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.OutgoingFTP.name)

def out_ftp(session, cluster_id, id):
    """ An outgoing FTP connection.
    """
    return _out_ftp(session, cluster_id).\
        filter(m.OutgoingFTP.id==id).\
        one()

@needs_columns
def out_ftp_list(session, cluster_id, needs_columns=False):
    """ Outgoing FTP connections.
    """
    return _out_ftp(session, cluster_id)

# ################################################################################################################################

def _service(session, cluster_id):
    return session.query(
        m.Service.id, m.Service.name, m.Service.is_active,
        m.Service.impl_name, m.Service.is_internal, m.Service.slow_threshold).\
        filter(m.Cluster.id==m.Service.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.Service.name)

def service(session, cluster_id, id):
    """ A service.
    """
    return _service(session, cluster_id).\
        filter(m.Service.id==id).\
        one()

@needs_columns
def service_list(session, cluster_id, return_internal=True, needs_columns=False):
    """ All services.
    """
    result = _service(session, cluster_id)
    if not return_internal:
        result = result.filter(not_(m.Service.name.startswith('zato')))
    return result

# ################################################################################################################################

def _delivery_definition(session, cluster_id):
    return session.query(m.DeliveryDefinitionBase).\
        filter(m.Cluster.id==m.DeliveryDefinitionBase.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.DeliveryDefinitionBase.name)

def delivery_definition_list(session, cluster_id, target_type=None):
    """ Returns a list of delivery definitions for a given target type.
    """
    def_list = _delivery_definition(session, cluster_id)

    if target_type:
        def_list = def_list.\
            filter(m.DeliveryDefinitionBase.target_type==target_type)

    return def_list

# ################################################################################################################################

def delivery_count_by_state(session, def_id):
    return session.query(m.Delivery.state, func.count(m.Delivery.state)).\
        filter(m.Delivery.definition_id==def_id).\
        group_by(m.Delivery.state)

def delivery_list(session, cluster_id, def_name, state, start=None, stop=None, needs_payload=False):
    columns = [
        m.DeliveryDefinitionBase.name.label('def_name'),
        m.DeliveryDefinitionBase.target_type,
        m.Delivery.task_id,
        m.Delivery.creation_time.label('creation_time_utc'),
        m.Delivery.last_used.label('last_used_utc'),
        m.Delivery.source_count,
        m.Delivery.target_count,
        m.Delivery.resubmit_count,
        m.Delivery.state,
        m.DeliveryDefinitionBase.retry_repeats,
        m.DeliveryDefinitionBase.check_after,
        m.DeliveryDefinitionBase.retry_seconds
    ]

    if needs_payload:
        columns.extend([m.DeliveryPayload.payload, m.Delivery.args, m.Delivery.kwargs])

    q = session.query(*columns).\
        filter(m.DeliveryDefinitionBase.id==m.Delivery.definition_id).\
        filter(m.DeliveryDefinitionBase.cluster_id==cluster_id).\
        filter(m.DeliveryDefinitionBase.name==def_name).\
        filter(m.Delivery.state.in_(state))

    if needs_payload:
        q = q.filter(m.DeliveryPayload.task_id==m.Delivery.task_id)

    if start:
        q = q.filter(m.Delivery.last_used >= start)

    if stop:
        q = q.filter(m.Delivery.last_used <= stop)

    q = q.order_by(m.Delivery.last_used.desc())

    return q

def delivery(session, task_id, target_def_class):
    return session.query(
        target_def_class.name.label('def_name'),
        target_def_class.target_type,
        m.Delivery.task_id,
        m.Delivery.creation_time.label('creation_time_utc'),
        m.Delivery.last_used.label('last_used_utc'),
        m.Delivery.source_count,
        m.Delivery.target_count,
        m.Delivery.resubmit_count,
        m.Delivery.state,
        target_def_class.retry_repeats,
        target_def_class.check_after,
        target_def_class.retry_seconds,
        m.DeliveryPayload.payload,
        m.Delivery.args,
        m.Delivery.kwargs,
        target_def_class.target,
        ).\
        filter(target_def_class.id==m.Delivery.definition_id).\
        filter(m.Delivery.task_id==task_id).\
        filter(m.DeliveryPayload.task_id==m.Delivery.task_id)

@needs_columns
def delivery_history_list(session, task_id, needs_columns=True):
    return session.query(
        m.DeliveryHistory.entry_type,
        m.DeliveryHistory.entry_time,
        m.DeliveryHistory.entry_ctx,
        m.DeliveryHistory.resubmit_count).\
        filter(m.DeliveryHistory.task_id==task_id).\
        order_by(m.DeliveryHistory.entry_time.desc())

# ################################################################################################################################

def _msg_list(class_, order_by, session, cluster_id, needs_columns=False):
    """ All the namespaces.
    """
    return session.query(
        class_.id, class_.name,
        class_.value).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==class_.cluster_id).\
        order_by(order_by)

@needs_columns
def namespace_list(session, cluster_id, needs_columns=False):
    """ All the namespaces.
    """
    return _msg_list(m.MsgNamespace, 'msg_ns.name', session, cluster_id, needs_columns)

@needs_columns
def xpath_list(session, cluster_id, needs_columns=False):
    """ All the XPaths.
    """
    return _msg_list(m.XPath, 'msg_xpath.name', session, cluster_id, needs_columns)

@needs_columns
def json_pointer_list(session, cluster_id, needs_columns=False):
    """ All the JSON Pointers.
    """
    return _msg_list(m.JSONPointer, 'msg_json_pointer.name', session, cluster_id, needs_columns)

# ################################################################################################################################

def _http_soap_audit(session, cluster_id, conn_id=None, start=None, stop=None, query=None, id=None, needs_req_payload=False):
    columns = [
        m.HTTSOAPAudit.id,
        m.HTTSOAPAudit.name.label('conn_name'),
        m.HTTSOAPAudit.cid,
        m.HTTSOAPAudit.transport,
        m.HTTSOAPAudit.connection,
        m.HTTSOAPAudit.req_time.label('req_time_utc'),
        m.HTTSOAPAudit.resp_time.label('resp_time_utc'),
        m.HTTSOAPAudit.user_token,
        m.HTTSOAPAudit.invoke_ok,
        m.HTTSOAPAudit.auth_ok,
        m.HTTSOAPAudit.remote_addr,
    ]

    if needs_req_payload:
        columns.extend([
            m.HTTSOAPAudit.req_headers, m.HTTSOAPAudit.req_payload, m.HTTSOAPAudit.resp_headers, m.HTTSOAPAudit.resp_payload
        ])

    q = session.query(*columns)
    
    if query:
        query = '%{}%'.format(query)
        q = q.filter(
            m.HTTSOAPAudit.cid.ilike(query) | \
            m.HTTSOAPAudit.req_headers.ilike(query) | m.HTTSOAPAudit.req_payload.ilike(query) | \
            m.HTTSOAPAudit.resp_headers.ilike(query) | m.HTTSOAPAudit.resp_payload.ilike(query)
        )

    if id:
        q = q.filter(m.HTTSOAPAudit.id == id)

    if conn_id:
        q = q.filter(m.HTTSOAPAudit.conn_id == conn_id)

    if start:
        q = q.filter(m.HTTSOAPAudit.req_time >= start)

    if stop:
        q = q.filter(m.HTTSOAPAudit.req_time <= start)

    q = q.order_by(m.HTTSOAPAudit.req_time.desc())

    return q

def http_soap_audit_item_list(ignored_self, session, cluster_id, conn_id, start, stop, query):
    return _http_soap_audit(session, cluster_id, conn_id, start, stop, query)

def http_soap_audit_item(session, cluster_id, id):
    return _http_soap_audit(session, cluster_id, id=id, needs_req_payload=True)

# ################################################################################################################################

def _cloud_openstack_swift(session, cluster_id):
    return session.query(m.OpenStackSwift).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.OpenStackSwift.cluster_id).\
        order_by(m.OpenStackSwift.name)

def cloud_openstack_swift(session, cluster_id, id):
    """ An OpenStack Swift connection.
    """
    return _cloud_openstack_swift(session, cluster_id).\
        filter(m.OpenStackSwift.id==id).\
        one()

@needs_columns
def cloud_openstack_swift_list(session, cluster_id, needs_columns=False):
    """ OpenStack Swift connections.
    """
    return _cloud_openstack_swift(session, cluster_id)

# ################################################################################################################################

def _cloud_aws_s3(session, cluster_id):
    return session.query(
        m.AWSS3.id, m.AWSS3.name, m.AWSS3.is_active, m.AWSS3.pool_size, m.AWSS3.address, m.AWSS3.debug_level, m.AWSS3.suppr_cons_slashes,
        m.AWSS3.content_type, m.AWSS3.metadata_, m.AWSS3.security_id, m.AWSS3.bucket, m.AWSS3.encrypt_at_rest, m.AWSS3.storage_class,
        m.SecurityBase.username, m.SecurityBase.password).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.AWSS3.security_id==m.SecurityBase.id).\
        order_by(m.AWSS3.name)

def cloud_aws_s3(session, cluster_id, id):
    """ An AWS S3 connection.
    """
    return _cloud_aws_s3(session, cluster_id).\
        filter(m.AWSS3.id==id).\
        one()

@needs_columns
def cloud_aws_s3_list(session, cluster_id, needs_columns=False):
    """ AWS S3 connections.
    """
    return _cloud_aws_s3(session, cluster_id)

# ################################################################################################################################

def _pubsub_topic(session, cluster_id):
    return session.query(m.PubSubTopic.id, m.PubSubTopic.name, m.PubSubTopic.is_active, m.PubSubTopic.max_depth).\
        filter(m.Cluster.id==m.PubSubTopic.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.PubSubTopic.name)

def pubsub_topic(session, cluster_id, id):
    """ A pub/sub topic.
    """
    return _pubsub_topic(session, cluster_id).\
        filter(m.PubSubTopic.id==id).\
        one()

@needs_columns
def pubsub_topic_list(session, cluster_id, needs_columns=False):
    """ All pub/sub topics.
    """
    return _pubsub_topic(session, cluster_id)

def pubsub_default_client(session, cluster_id, name):
    """ Returns a client ID of a given name used internally for pub/sub.
    """
    return session.query(m.HTTPBasicAuth.id, m.HTTPBasicAuth.name).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.HTTPBasicAuth.cluster_id).\
        filter(m.HTTPBasicAuth.name==name).\
        first()

# ################################################################################################################################

def _pubsub_producer(session, cluster_id, needs_columns=False):
    return session.query(
        m.PubSubProducer.id,
        m.PubSubProducer.is_active,
        m.SecurityBase.id.label('client_id'),
        m.SecurityBase.name,
        m.SecurityBase.sec_type,
        m.PubSubTopic.name.label('topic_name')).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.PubSubProducer.topic_id==m.PubSubTopic.id).\
        filter(m.PubSubProducer.cluster_id==m.Cluster.id).\
        filter(m.PubSubProducer.sec_def_id==m.SecurityBase.id).\
        order_by(m.SecurityBase.sec_type, m.SecurityBase.name)

@needs_columns
def pubsub_producer_list(session, cluster_id, topic_name, needs_columns=False):
    """ All pub/sub producers.
    """
    response = _pubsub_producer(session, cluster_id, needs_columns)
    if topic_name:
        response = response.filter(m.PubSubTopic.name==topic_name)
    return response

# ################################################################################################################################

def _pubsub_consumer(session, cluster_id, needs_columns=False):
    return session.query(
        m.PubSubConsumer.id,
        m.PubSubConsumer.is_active,
        m.PubSubConsumer.max_depth,
        m.PubSubConsumer.sub_key,
        m.PubSubConsumer.delivery_mode,
        m.PubSubConsumer.callback_id,
        m.PubSubConsumer.callback_type,
        m.HTTPSOAP.name.label('callback_name'),
        m.HTTPSOAP.soap_version,
        m.SecurityBase.id.label('client_id'),
        m.SecurityBase.name,
        m.SecurityBase.sec_type,
        m.PubSubTopic.name.label('topic_name')).\
        outerjoin(m.HTTPSOAP, m.HTTPSOAP.id==m.PubSubConsumer.callback_id).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.PubSubConsumer.topic_id==m.PubSubTopic.id).\
        filter(m.PubSubConsumer.cluster_id==m.Cluster.id).\
        filter(m.PubSubConsumer.sec_def_id==m.SecurityBase.id).\
        order_by(m.SecurityBase.sec_type, m.SecurityBase.name)

@needs_columns
def pubsub_consumer_list(session, cluster_id, topic_name, needs_columns=False):
    """ All pub/sub consumers.
    """
    response = _pubsub_consumer(session, cluster_id, needs_columns)
    if topic_name:
        response = response.filter(m.PubSubTopic.name==topic_name)
    return response

# ################################################################################################################################

def _notif_cloud_openstack_swift(session, cluster_id, needs_password):
    """ OpenStack Swift notifications.
    """

    columns = [m.NotificationOpenStackSwift.id, m.NotificationOpenStackSwift.name, m.NotificationOpenStackSwift.is_active, m.NotificationOpenStackSwift.notif_type, m.NotificationOpenStackSwift.def_id, m.NotificationOpenStackSwift.containers,
        m.NotificationOpenStackSwift.interval, m.NotificationOpenStackSwift.name_pattern, m.NotificationOpenStackSwift.name_pattern_neg, m.NotificationOpenStackSwift.get_data, m.NotificationOpenStackSwift.get_data_patt,
        m.NotificationOpenStackSwift.get_data_patt_neg, m.OpenStackSwift.name.label('def_name'), m.Service.name.label('service_name')]

    #if needs_password:

    return session.query(*columns).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.NotificationOpenStackSwift.cluster_id).\
        filter(m.NotificationOpenStackSwift.def_id==m.OpenStackSwift.id).\
        filter(m.NotificationOpenStackSwift.service_id==m.Service.id).\
        order_by(m.NotificationOpenStackSwift.name)

def notif_cloud_openstack_swift(session, cluster_id, id, needs_password=False):
    """ An OpenStack Swift notification definition.
    """
    return _notif_cloud_openstack_swift(session, cluster_id, needs_password).\
        filter(m.NotificationOpenStackSwift.id==id).\
        one()

@needs_columns
def notif_cloud_openstack_swift_list(session, cluster_id, needs_password=False, needs_columns=False):
    """ OpenStack Swift connection definitions.
    """
    return _notif_cloud_openstack_swift(session, cluster_id, needs_password)

# ################################################################################################################################

def _notif_sql(session, cluster_id, needs_password):
    """ SQL notifications.
    """

    columns = [m.NotificationSQL.id, m.NotificationSQL.is_active, m.NotificationSQL.name, m.NotificationSQL.query, m.NotificationSQL.notif_type, m.NotificationSQL.interval, \
        m.NotificationSQL.def_id, m.SQLConnectionPool.name.label('def_name'), m.Service.name.label('service_name')]

    if needs_password:
        columns.append(m.SQLConnectionPool.password)

    return session.query(*columns).\
        filter(m.Cluster.id==m.NotificationSQL.cluster_id).\
        filter(m.SQLConnectionPool.id==m.NotificationSQL.def_id).\
        filter(m.Service.id==m.NotificationSQL.service_id).\
        filter(m.Cluster.id==cluster_id)

@needs_columns
def notif_sql_list(session, cluster_id, needs_password=False, needs_columns=False):
    """ All the SQL notifications.
    """
    return _notif_sql(session, cluster_id, needs_password)

# ################################################################################################################################

def _search_es(session, cluster_id):
    """ m.ElasticSearch connections.
    """
    return session.query(m.ElasticSearch).\
        filter(m.Cluster.id==m.ElasticSearch.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.ElasticSearch.name)

@needs_columns
def search_es_list(session, cluster_id, needs_columns=False):
    """ All the m.ElasticSearch connections.
    """
    return _search_es(session, cluster_id)

# ################################################################################################################################

def _search_solr(session, cluster_id):
    """ m.Solr sonnections.
    """
    return session.query(m.Solr).\
        filter(m.Cluster.id==m.Solr.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.Solr.name)

@needs_columns
def search_solr_list(session, cluster_id, needs_columns=False):
    """ All the m.Solr connections.
    """
    return _search_solr(session, cluster_id)

# ################################################################################################################################

def _server(session, cluster_id):
    return session.query(
        m.Server.id, m.Server.name, m.Server.bind_host, m.Server.bind_port, m.Server.last_join_status, m.Server.last_join_mod_date,
        m.Server.last_join_mod_by, m.Server.up_status, m.Server.up_mod_date, m.Cluster.name.label('cluster_name')).\
        filter(m.Cluster.id==m.Server.cluster_id).\
        filter(m.Cluster.id==cluster_id).\
        order_by(m.Server.name)

@needs_columns
def server_list(session, cluster_id, needs_columns=False):
    """ All the servers defined on a cluster.
    """
    return _server(session, cluster_id)

# ################################################################################################################################

def _cassandra_conn(session, cluster_id):
    return session.query(m.CassandraConn).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.CassandraConn.cluster_id).\
        order_by(m.CassandraConn.name)

def cassandra_conn(session, cluster_id, id):
    """ A Cassandra connection definition.
    """
    return _cassandra_conn(session, cluster_id).\
        filter(m.CassandraConn.id==id).\
        one()

@needs_columns
def cassandra_conn_list(session, cluster_id, needs_columns=False):
    """ A list of Cassandra connection definitions.
    """
    return _cassandra_conn(session, cluster_id)

# ################################################################################################################################

def _cassandra_query(session, cluster_id):
    return session.query(
        m.CassandraQuery.id, m.CassandraQuery.name, m.CassandraQuery.value,
        m.CassandraQuery.is_active, m.CassandraQuery.cluster_id,
        m.CassandraConn.name.label('def_name'),
        m.CassandraConn.id.label('def_id'),
        ).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.CassandraQuery.cluster_id).\
        filter(m.CassandraConn.id==m.CassandraQuery.def_id).\
        order_by(m.CassandraQuery.name)

def cassandra_query(session, cluster_id, id):
    """ A Cassandra prepared statement.
    """
    return _cassandra_query(session, cluster_id).\
        filter(m.CassandraQuery.id==id).\
        one()

@needs_columns
def cassandra_query_list(session, cluster_id, needs_columns=False):
    """ A list of Cassandra prepared statements.
    """
    return _cassandra_query(session, cluster_id)

# ################################################################################################################################

def _email_smtp(session, cluster_id):
    return session.query(m.SMTP).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.SMTP.cluster_id).\
        order_by(m.SMTP.name)

def email_smtp(session, cluster_id, id):
    """ An m.SMTP connection.
    """
    return _email_smtp(session, cluster_id).\
        filter(m.SMTP.id==id).\
        one()

@needs_columns
def email_smtp_list(session, cluster_id, needs_columns=False):
    """ A list of m.SMTP connections.
    """
    return _email_smtp(session, cluster_id)

# ################################################################################################################################

def _email_imap(session, cluster_id):
    return session.query(m.IMAP).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.IMAP.cluster_id).\
        order_by(m.IMAP.name)

def email_imap(session, cluster_id, id):
    """ An m.IMAP connection.
    """
    return _email_imap(session, cluster_id).\
        filter(m.IMAP.id==id).\
        one()

@needs_columns
def email_imap_list(session, cluster_id, needs_columns=False):
    """ A list of m.IMAP connections.
    """
    return _email_imap(session, cluster_id)

# ################################################################################################################################

def _rbac_permission(session, cluster_id):
    return session.query(m.RBACPermission).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.RBACPermission.cluster_id).\
        order_by(m.RBACPermission.name)

def rbac_permission(session, cluster_id, id):
    """ An RBAC permission.
    """
    return _rbac_permission(session, cluster_id).\
        filter(m.RBACPermission.id==id).\
        one()

@needs_columns
def rbac_permission_list(session, cluster_id, needs_columns=False):
    """ A list of RBAC permissions.
    """
    return _rbac_permission(session, cluster_id)

# ################################################################################################################################

def _rbac_role(session, cluster_id):
    rbac_parent = aliased(m.RBACRole)
    return session.query(m.RBACRole.id, m.RBACRole.name, m.RBACRole.parent_id, rbac_parent.name.label('parent_name')).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.RBACRole.cluster_id).\
        outerjoin(rbac_parent, rbac_parent.id==m.RBACRole.parent_id).\
        order_by(m.RBACRole.name)

def rbac_role(session, cluster_id, id):
    """ An RBAC role.
    """
    return _rbac_role(session, cluster_id).\
        filter(m.RBACRole.id==id).\
        one()

@needs_columns
def rbac_role_list(session, cluster_id, needs_columns=False):
    """ A list of RBAC roles.
    """
    return _rbac_role(session, cluster_id)

# ################################################################################################################################

def _rbac_client_role(session, cluster_id):
    return session.query(m.RBACClientRole).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.RBACClientRole.cluster_id).\
        order_by(m.RBACClientRole.client_def)

def rbac_client_role(session, cluster_id, id):
    """ An individual mapping between a client and role.
    """
    return _rbac_client_role(session, cluster_id).\
        filter(m.RBACClientRole.id==id).\
        one()

@needs_columns
def rbac_client_role_list(session, cluster_id, needs_columns=False):
    """ A list of mappings between clients and roles.
    """
    return _rbac_client_role(session, cluster_id)

# ################################################################################################################################

def _rbac_role_permission(session, cluster_id):
    return session.query(m.RBACRolePermission).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.RBACRolePermission.cluster_id).\
        order_by(m.RBACRolePermission.role_id)

def rbac_role_permission(session, cluster_id, id):
    """ An individual permission for a given role against a service.
    """
    return _rbac_role_permission(session, cluster_id).\
        filter(m.RBACRolePermission.id==id).\
        one()

@needs_columns
def rbac_role_permission_list(session, cluster_id, needs_columns=False):
    """ A list of permissions for roles against services.
    """
    return _rbac_role_permission(session, cluster_id)

# ################################################################################################################################

def _out_odoo(session, cluster_id):
    return session.query(m.OutgoingOdoo).\
        filter(m.Cluster.id==cluster_id).\
        filter(m.Cluster.id==m.OutgoingOdoo.cluster_id).\
        order_by(m.OutgoingOdoo.name)

def out_odoo(session, cluster_id, id):
    """ An individual Odoo connection.
    """
    return _out_odoo(session, cluster_id).\
        filter(m.OutgoingOdoo.id==id).\
        one()

@needs_columns
def out_odoo_list(session, cluster_id, needs_columns=False):
    """ A list of Odoo connections.
    """
    return _out_odoo(session, cluster_id)

# ################################################################################################################################

def process_definition_base(session, cluster_id):
    return session.query(m.ProcDef).\
        filter(m.ProcDef.cluster_id==cluster_id)

def _process_definition(session, cluster_id):
    return process_definition_base(session, cluster_id).\
        order_by(m.ProcDef.name, m.ProcDef.version)

def process_definition(session, cluster_id, id):
    """ An individual process definition.
    """
    return _process_definition(session, cluster_id).\
        filter(m.ProcDef.id==id).\
        one()

@needs_columns
def process_definition_list(session, cluster_id, needs_columns=False):
    """ A list of process definitions.
    """
    return _process_definition(session, cluster_id)

# ################################################################################################################################
