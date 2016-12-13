# -*- coding: utf-8 -*-

"""
Copyright (C) 2016, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# Utilities taken from zato.common.util directly since ExeAgent is a standalone entity.

# stdlib
import os

# configobj
from configobj import ConfigObj

# ################################################################################################################################

def absjoin(base, path):
    """ Turns a path into an absolute path if it's relative to the base location. If the path is already an absolute path,
    it is returned as-is.
    """
    if isabs(path):
        return path

    return abspath(join(base, path))

# ################################################################################################################################

def get_config(repo_location, config_name, bunchified=True, needs_user_config=True):
    """ Returns the configuration object. Will load additional user-defined config files,
    if any are available at all.
    """
    conf = ConfigObj(os.path.join(repo_location, config_name))
    conf = bunchify(conf) if bunchified else conf

    if needs_user_config:
        conf.user_config_items = {}

        user_config = conf.get('user_config')
        if user_config:
            for name, path in user_config.items():
                path = absolutize(path, repo_location)
                if not os.path.exists(path):
                    logger.warn('User config not found `%s`, name:`%s`', path, name)
                else:
                    user_conf = ConfigObj(path)
                    user_conf = bunchify(user_conf) if bunchified else user_conf
                    conf.user_config_items[name] = user_conf

    return conf

# ################################################################################################################################

def store_pidfile(component_dir):
    open(os.path.join(component_dir, 'pidfile'), 'w').write('{}'.format(os.getpid()))

# ################################################################################################################################
