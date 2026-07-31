"""
Project-level urls.py

Wires the sync app's urls.py in under /api/, matching the
"baseurl" + "endpoint" combination sync.py posts to
(e.g. baseurl="http://localhost" + endpoint="/api/sync/product/").

Adjust the app name in include() below to match whatever you name
the Django app these models/views/urls live in (e.g. "ecommerce_sync").
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("app1.urls")),  # TODO: rename to your actual app name
]