# -*- coding: utf-8 -*-

"""
Copyright (C) 2016 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
import os
from unittest import TestCase

# SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker

# Zato
from zato.model.sql import Base

class TestORM(TestCase):

    def setUp(self):
        db_path = '/home/dsuch/tmp/zzz.db'

        if os.path.exists(db_path):
            os.unlink(db_path)

        db_url = 'postgresql+pg8000://zato1:zato1@localhost/zato1'
        #db_url = 'sqlite:////home/dsuch/tmp/zzz.db'
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)

        self.session = sessionmaker()
        self.session.configure(bind=engine)

    def test_create_models(self):

        pass