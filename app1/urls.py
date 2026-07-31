from django.urls import path
from . import views

urlpatterns = [
    # --- Write endpoints (POST) - used by sync.py ---
    path("sync/productproduct/", views.ProductProductSyncView.as_view(), name="sync-productproduct"),
    path("sync/productbrand/", views.ProductBrandSyncView.as_view(), name="sync-productbrand"),
    path("sync/master/", views.MasterSyncView.as_view(), name="sync-master"),
    path("sync/product/", views.ProductSyncView.as_view(), name="sync-product"),
    path("sync/productphoto/", views.ProductPhotoSyncView.as_view(), name="sync-productphoto"),
    path("sync/productbatch/", views.ProductBatchSyncView.as_view(), name="sync-productbatch"),
    path("sync/servicemaster/", views.ServiceMasterSyncView.as_view(), name="sync-servicemaster"),
    path("sync/users/", views.UserAccountSyncView.as_view(), name="sync-users"),

    # --- Read endpoints (GET) ---
    path("productproduct/", views.ProductProductListView.as_view(), name="list-productproduct"),
    path("productproduct/<str:name>/", views.ProductProductDetailView.as_view(), name="detail-productproduct"),

    path("productbrand/", views.ProductBrandListView.as_view(), name="list-productbrand"),
    path("productbrand/<str:name>/", views.ProductBrandDetailView.as_view(), name="detail-productbrand"),

    path("master/", views.MasterListView.as_view(), name="list-master"),
    path("master/<str:code>/", views.MasterDetailView.as_view(), name="detail-master"),

    path("product/", views.ProductListView.as_view(), name="list-product"),
    path("product/<str:code>/", views.ProductDetailView.as_view(), name="detail-product"),

    path("productphoto/", views.ProductPhotoListView.as_view(), name="list-productphoto"),
    path("productbatch/", views.ProductBatchListView.as_view(), name="list-productbatch"),
    path("servicemaster/", views.ServiceMasterListView.as_view(), name="list-servicemaster"),

    path("users/", views.UserAccountListView.as_view(), name="list-users"),
    path("users/<str:id>/", views.UserAccountDetailView.as_view(), name="detail-users"),
]