from django.forms.models import model_to_dict
from django.core.paginator import Paginator
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from .models import (
    ProductProduct,
    ProductBrand,
    Master,
    Product,
    ProductPhoto,
    ProductBatch,
    ServiceMaster,
    UserAccount,
)


# ---------------------------------------------------------------------------
# Write side (POST) - sync.py pushes rows here
#
# Every sync view below now fully replaces the table's contents on each
# sync run: the table is wiped once (on chunk index 0) and then every
# chunk in that run is inserted fresh. This means a row that no longer
# exists in the source data will also disappear from Django after the
# next sync - the table always mirrors exactly what the source sent.
# ---------------------------------------------------------------------------

class BaseUpsertSyncView(APIView):
    """
    Upsert for tables that have a real primary key, with full-replace
    semantics across a sync run.

    sync.py sends the full filtered table split into chunks. On the
    first chunk (X-Chunk-Index: 0) the table is wiped before inserting,
    so upsert conflict handling still applies within a run (in case the
    same row appears twice across chunks) but nothing from a *previous*
    run survives.

    Subclasses set:
      - model: the Django model to sync into
      - pk_field: the model's primary key field name (also the unique key)
      - update_fields: list of field names to overwrite on conflict
      - key_map: optional dict to rename incoming JSON keys to model field
                 names before saving (e.g. text3 -> size)
    """
    permission_classes = [AllowAny]  # TODO: add auth
    model = None
    pk_field = None
    update_fields = []
    key_map = {}

    def clean_row(self, row):
        cleaned = dict(row)
        for source_key, target_key in self.key_map.items():
            if source_key in cleaned:
                cleaned[target_key] = cleaned.pop(source_key)
        return cleaned

    def post(self, request):
        rows = request.data
        if not isinstance(rows, list):
            return Response(
                {"error": "Expected a list of rows."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            chunk_index = int(request.headers.get("X-Chunk-Index", "0"))
        except ValueError:
            chunk_index = 0

        if chunk_index == 0:
            self.model.objects.all().delete()

        objs = []
        skipped = []
        for row in rows:
            cleaned = self.clean_row(row)
            if cleaned.get(self.pk_field) in (None, ""):
                skipped.append({"row": row, "error": f"Missing {self.pk_field}"})
                continue
            objs.append(self.model(**cleaned))

        if objs:
            self.model.objects.bulk_create(
                objs,
                update_conflicts=True,
                unique_fields=[self.pk_field],
                update_fields=self.update_fields,
            )

        return Response(
            {
                "synced": len(objs),
                "skipped": skipped,
                "total_received": len(rows),
                "chunk_index": chunk_index,
                "table_wiped_this_request": chunk_index == 0,
            },
            status=status.HTTP_200_OK,
        )


class BaseReplaceSyncView(APIView):
    """
    For tables with no natural key. First chunk received in a sync run
    wipes the table; every chunk bulk-inserts. sync.py always sends the
    full table (filtered by its WHERE clause), so this keeps the table
    matching the source exactly without duplicate growth.

    Subclasses set:
      - model: the Django model to sync into
      - key_map: optional rename map applied per row before saving
    """
    permission_classes = [AllowAny]  # TODO: add auth
    model = None
    key_map = {}

    def clean_row(self, row):
        cleaned = dict(row)
        for source_key, target_key in self.key_map.items():
            if source_key in cleaned:
                cleaned[target_key] = cleaned.pop(source_key)
        return cleaned

    def post(self, request):
        rows = request.data
        if not isinstance(rows, list):
            return Response(
                {"error": "Expected a list of rows."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            chunk_index = int(request.headers.get("X-Chunk-Index", "0"))
        except ValueError:
            chunk_index = 0

        if chunk_index == 0:
            self.model.objects.all().delete()

        objs = [self.model(**self.clean_row(row)) for row in rows]
        if objs:
            self.model.objects.bulk_create(objs)

        return Response(
            {
                "synced": len(objs),
                "total_received": len(rows),
                "chunk_index": chunk_index,
                "table_wiped_this_request": chunk_index == 0,
            },
            status=status.HTTP_200_OK,
        )


class ProductProductSyncView(BaseUpsertSyncView):
    model = ProductProduct
    pk_field = "name"
    update_fields = ["url"]


class ProductBrandSyncView(BaseUpsertSyncView):
    model = ProductBrand
    pk_field = "name"
    update_fields = ["url"]


class MasterSyncView(BaseUpsertSyncView):
    model = Master
    pk_field = "code"
    update_fields = [
        "name", "super_code", "address", "place", "city", "state",
        "phone", "phone2", "fax", "remarkcolumntitle", "area", "gstin",
    ]


class ProductSyncView(BaseUpsertSyncView):
    model = Product
    pk_field = "code"
    key_map = {"text3": "size", "text5": "sub_category"}
    update_fields = [
        "name", "size", "sub_category", "unit", "taxcode", "company",
        "product", "brand", "text6", "nameinsl", "properties",
        "defected",
    ]


class ProductPhotoSyncView(BaseReplaceSyncView):
    model = ProductPhoto


class ProductBatchSyncView(BaseReplaceSyncView):
    model = ProductBatch


class ServiceMasterSyncView(BaseReplaceSyncView):
    model = ServiceMaster


class UserAccountSyncView(BaseUpsertSyncView):
    """
    Source column "pass" maps to model field "password" ("pass" is a
    Python keyword, can't be used as a field name directly).
    """
    model = UserAccount
    pk_field = "id"
    key_map = {"pass": "password"}
    update_fields = ["password", "role"]


# ---------------------------------------------------------------------------
# Read side (GET) - list / detail, plain JSON, no DRF serializers
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500


def _paginated_response(request, queryset, exclude_fields=None):
    """
    Shared pagination + serialization helper for list views.
    ?page=1&page_size=50
    """
    try:
        page_size = min(int(request.GET.get("page_size", DEFAULT_PAGE_SIZE)), MAX_PAGE_SIZE)
    except ValueError:
        page_size = DEFAULT_PAGE_SIZE

    try:
        page_number = int(request.GET.get("page", 1))
    except ValueError:
        page_number = 1

    paginator = Paginator(queryset, page_size)
    page = paginator.get_page(page_number)

    results = []
    for obj in page.object_list:
        data = model_to_dict(obj)
        if exclude_fields:
            for field in exclude_fields:
                data.pop(field, None)
        results.append(data)

    return JsonResponse({
        "count": paginator.count,
        "page": page.number,
        "num_pages": paginator.num_pages,
        "page_size": page_size,
        "results": results,
    })


def _detail_response(obj, exclude_fields=None):
    if obj is None:
        return JsonResponse({"error": "Not found."}, status=404)
    data = model_to_dict(obj)
    if exclude_fields:
        for field in exclude_fields:
            data.pop(field, None)
    return JsonResponse(data)


class ProductProductListView(APIView):
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request):
        qs = ProductProduct.objects.all().order_by("name")
        return _paginated_response(request, qs)


class ProductProductDetailView(APIView):
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request, name):
        obj = ProductProduct.objects.filter(pk=name).first()
        return _detail_response(obj)


class ProductBrandListView(APIView):
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request):
        qs = ProductBrand.objects.all().order_by("name")
        return _paginated_response(request, qs)


class ProductBrandDetailView(APIView):
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request, name):
        obj = ProductBrand.objects.filter(pk=name).first()
        return _detail_response(obj)


class MasterListView(APIView):
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request):
        qs = Master.objects.all().order_by("code")
        return _paginated_response(request, qs)


class MasterDetailView(APIView):
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request, code):
        obj = Master.objects.filter(pk=code).first()
        return _detail_response(obj)


class ProductListView(APIView):
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request):
        qs = Product.objects.all().order_by("code")
        return _paginated_response(request, qs)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request, code):
        obj = Product.objects.filter(pk=code).first()
        return _detail_response(obj)


class ProductPhotoListView(APIView):
    """Supports ?code=P100 to get all photos for one product."""
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request):
        qs = ProductPhoto.objects.all().order_by("slno")
        code = request.GET.get("code")
        if code:
            qs = qs.filter(code=code)
        return _paginated_response(request, qs)


class ProductBatchListView(APIView):
    """Supports ?productcode=P100 to get all batches for one product."""
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request):
        qs = ProductBatch.objects.all().order_by("slno")
        productcode = request.GET.get("productcode")
        if productcode:
            qs = qs.filter(productcode=productcode)
        return _paginated_response(request, qs)


class ServiceMasterListView(APIView):
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request):
        qs = ServiceMaster.objects.all().order_by("slno")
        return _paginated_response(request, qs)


class UserAccountListView(APIView):
    """password is never included in the response."""
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request):
        qs = UserAccount.objects.all().order_by("id")
        return _paginated_response(request, qs, exclude_fields=["password"])


class UserAccountDetailView(APIView):
    permission_classes = [AllowAny]  # TODO: add auth

    def get(self, request, id):
        obj = UserAccount.objects.filter(pk=id).first()
        return _detail_response(obj, exclude_fields=["password"])