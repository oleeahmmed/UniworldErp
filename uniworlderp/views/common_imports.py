# common_imports.py

from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView,View
from django.urls import reverse_lazy,reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import PermissionRequiredMixin,LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect,render
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from datetime import timedelta
from django.db.models import Prefetch

from django.db import transaction
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from django.db.models import F,Q, Value, Case, When,Sum,Count,Max,Min
from django.db.models.functions import Concat
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation
import uuid
