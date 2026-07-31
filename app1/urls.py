"""
URLs for SYSMAC ECOMMERCE SYNC.

These paths match the "endpoint" values already set in sync.py's
TABLES list - no need to change sync.py once this is wired into
the project's main urls.py.
"""

from django.urls import path
from . import views

urlpatterns = [
    path("sync/productproduct/", views.ProductProductSyncView.as_view(), name="sync-productproduct"),
    path("sync/productbrand/", views.ProductBrandSyncView.as_view(), name="sync-productbrand"),
    path("sync/master/", views.MasterSyncView.as_view(), name="sync-master"),
    path("sync/product/", views.ProductSyncView.as_view(), name="sync-product"),
    path("sync/productphoto/", views.ProductPhotoSyncView.as_view(), name="sync-productphoto"),
    path("sync/productbatch/", views.ProductBatchSyncView.as_view(), name="sync-productbatch"),
    path("sync/servicemaster/", views.ServiceMasterSyncView.as_view(), name="sync-servicemaster"),
    path("sync/users/", views.UserAccountSyncView.as_view(), name="sync-users"),
]