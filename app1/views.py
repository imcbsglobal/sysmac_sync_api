"""
Views for SYSMAC ECOMMERCE SYNC.

Each endpoint receives a JSON list of rows (a chunk from sync.py) and
writes them in bulk - one or two queries total, not one query per row.
That's the difference between ~5 rows/sec and thousands of rows/sec.

Two strategies, depending on whether the table has a real primary key:

1. Tables with a natural key (ProductProduct.name, ProductBrand.name,
   Master.code, Product.code): bulk_create(..., update_conflicts=True).
   This is a real upsert - insert new rows, update existing ones whose
   key already exists - done in one query per chunk.

2. Tables with no natural key (ProductPhoto, ProductBatch,
   ServiceMaster - their real PK is just an internal slno autofield):
   there's nothing to "conflict" on, so each sync wipes the table and
   bulk-inserts fresh. This also avoids these tables growing forever
   with duplicate rows every time sync.py runs.

No auth wired in yet - AllowAny for now. Swap in JWT/API key auth
once that's decided, same as MagnetPro's other sync endpoints.
"""

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


class BaseUpsertSyncView(APIView):
    """
    Bulk upsert for tables that have a real primary key.
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

        is_first_chunk = request.data and int(request.headers.get("X-Chunk-Index", "0")) == 0
        if is_first_chunk:
            self.model.objects.all().delete()

        objs = [self.model(**self.clean_row(row)) for row in rows]
        if objs:
            self.model.objects.bulk_create(objs)

        return Response(
            {"synced": len(objs), "total_received": len(rows)},
            status=status.HTTP_200_OK,
        )


class ProductProductSyncView(BaseUpsertSyncView):
    model = ProductProduct
    pk_field = "name"
    update_fields = ["settings", "url"]


class ProductBrandSyncView(BaseUpsertSyncView):
    model = ProductBrand
    pk_field = "name"
    update_fields = ["settings", "url"]


class MasterSyncView(BaseUpsertSyncView):
    model = Master
    pk_field = "code"
    update_fields = [
        "name", "super_code", "address", "place", "city", "state",
        "phone", "phone2", "fax", "remarkcolumntitle", "area", "gstin",
    ]


class ProductSyncView(BaseUpsertSyncView):
    """Source columns text3/text5 map to model fields size/sub_category."""
    model = Product
    pk_field = "code"
    key_map = {"text3": "size", "text5": "sub_category"}
    update_fields = [
        "name", "size", "sub_category", "unit", "taxcode", "company",
        "product", "brand", "text6", "nameinsl", "settings", "properties",
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