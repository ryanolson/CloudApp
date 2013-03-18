# -*- coding: utf-8 -*-

from .models import *
from .models import __all__ as models_all
from .decorators import load_user
#from .views import auth as authWWW
from .endpoints import api as authAPI

__all__ = ['authAPI','load_user']
__all__.extend( models_all )
