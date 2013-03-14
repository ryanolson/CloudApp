# -*- coding: utf-8 -*-
from flask.ext.principal import Permission, UserNeed, RoleNeed

valid_user = Permission(UserNeed('Valid'))
admin_user = Permission(RoleNeed('Admin'))
