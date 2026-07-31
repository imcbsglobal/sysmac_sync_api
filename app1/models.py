from django.db import models


class ProductProduct(models.Model):
    """
    Source: acc_productproduct
    WHERE condition: settings LIKE '%##EC##%' AND settings LIKE '%##EU##%'
    """
    name = models.CharField(max_length=30, primary_key=True)
    settings = models.CharField(max_length=300, null=True, blank=True)
    url = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = "acc_productproduct"
        managed = False  # table already exists in postgres, created outside Django migrations

    def __str__(self):
        return self.name


class ProductBrand(models.Model):
    """
    Source: acc_productbrand
    WHERE condition: settings LIKE '%##EC##%' AND settings LIKE '%##EU##%'
    """
    name = models.CharField(max_length=30, primary_key=True)
    settings = models.CharField(max_length=300, null=True, blank=True)
    url = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = "acc_productbrand"
        managed = False  # table already exists in postgres, created outside Django migrations

    def __str__(self):
        return self.name


class Master(models.Model):
    """
    Source: acc_master
    WHERE condition: super_code = 'debto'
    """
    code = models.CharField(max_length=30, primary_key=True)
    name = models.CharField(max_length=250)
    super_code = models.CharField(max_length=5, null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    place = models.CharField(max_length=60, null=True, blank=True)
    city = models.CharField(max_length=80, null=True, blank=True)
    state = models.CharField(max_length=40, null=True, blank=True)
    phone = models.CharField(max_length=60, null=True, blank=True)
    phone2 = models.CharField(max_length=60, null=True, blank=True)
    fax = models.CharField(max_length=30, null=True, blank=True)
    remarkcolumntitle = models.CharField(max_length=20, null=True, blank=True)
    area = models.CharField(max_length=30, null=True, blank=True)
    gstin = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        db_table = "acc_master"
        managed = False  # table already exists in postgres, created outside Django migrations

    def __str__(self):
        return f"{self.code} - {self.name}"


class Product(models.Model):
    """
    Source: acc_product
    WHERE condition: settings LIKE '%##EC##%'
    text3 = size, text5 = sub category
    """
    code = models.CharField(max_length=30, primary_key=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    size = models.CharField(max_length=60, null=True, blank=True, db_column="text3")
    sub_category = models.CharField(max_length=60, null=True, blank=True, db_column="text5")
    unit = models.CharField(max_length=10, null=True, blank=True)
    taxcode = models.CharField(max_length=5, null=True, blank=True)
    company = models.CharField(max_length=30, null=True, blank=True)
    product = models.CharField(max_length=30, null=True, blank=True)
    brand = models.CharField(max_length=30, null=True, blank=True)
    text6 = models.CharField(max_length=40, null=True, blank=True)
    nameinsl = models.CharField(max_length=350, null=True, blank=True)
    settings = models.CharField(max_length=300, null=True, blank=True)
    properties = models.CharField(max_length=900, null=True, blank=True)

    class Meta:
        db_table = "acc_product"
        managed = False  # table already exists in postgres, created outside Django migrations

    def __str__(self):
        return f"{self.code} - {self.name}"


class ProductPhoto(models.Model):
    """
    Source: acc_productphoto
    No WHERE condition - all rows sync.
    """
    slno = models.AutoField(primary_key=True)
    code = models.CharField(max_length=30, null=True, blank=True)
    url2 = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = "acc_productphoto"
        managed = False  # table already exists in postgres, created outside Django migrations

    def __str__(self):
        return f"{self.code} - photo {self.slno}"


class ProductBatch(models.Model):
    """
    Source: acc_productbatch
    WHERE condition: settings LIKE '%##EC##%'
    """
    slno = models.AutoField(primary_key=True)
    productcode = models.CharField(max_length=30)
    salesprice = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    secondprice = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    thirdprice = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    fourthprice = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    nlc1 = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    barcode = models.CharField(max_length=35, null=True, blank=True)
    bmrp = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    settings = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = "acc_productbatch"
        managed = False  # table already exists in postgres, created outside Django migrations

    def __str__(self):
        return f"{self.productcode} batch {self.slno}"


class ServiceMaster(models.Model):
    """
    Source: acc_tt_servicemaster
    WHERE condition: type = section and area
    """
    slno = models.AutoField(primary_key=True)
    type = models.CharField(max_length=20, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    code = models.CharField(max_length=30, null=True, blank=True)
    url = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = "acc_tt_servicemaster"
        managed = False  # table already exists in postgres, created outside Django migrations

    def __str__(self):
        return f"{self.type} - {self.name}"


class UserAccount(models.Model):
    """
    Source: acc_users
    WHERE condition: role IN ('level1', 'level2', 'level3')

    Source PK is composite (id, pass). Django models need a single pk,
    so "id" is used as the pk here - update if id alone isn't actually
    unique in the source data.
    """
    id = models.CharField(max_length=30, primary_key=True, db_column="id")
    password = models.CharField(max_length=100, db_column="pass")
    role = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        db_table = "acc_users"
        managed = False  # table already exists in postgres, created outside Django migrations

    def __str__(self):
        return f"{self.id} ({self.role})"