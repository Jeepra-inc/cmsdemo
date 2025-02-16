from django.db import models
from django.contrib.auth import get_user_model
from autoslug import AutoSlugField
from taggit.managers import TaggableManager

from django.db import models
from autoslug import AutoSlugField

# BaseCategory Model for Shared Fields
class BaseCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from='name', unique=True)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.URLField(blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


# Category Model for Posts and Pages with Hierarchy
class Category(BaseCategory):
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='children',
        help_text="Optional parent category to support hierarchy."
    )

    class Meta:
        verbose_name_plural = "Categories"


# Product Category Model (specifically for Products)
class ProductCategory(BaseCategory):
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='children'
    )

    class Meta:
        verbose_name_plural = "Product Categories"


# Service Category Model (specifically for Services)
class ServiceCategory(BaseCategory):
    class Meta:
        verbose_name_plural = "Service Categories"



# BasePage Model for Shared Fields
class BasePage(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('password_protected', 'Password Protected'),
    ]

    EDITOR_MODE_CHOICES = [
        ('classic', 'Classic'),
        ('builder', 'Builder'),
    ]

    # Shared Metadata Fields
    name = models.CharField(max_length=255)
    content = models.JSONField(blank=True, null=True)  # Updated to JSONField
    slug = AutoSlugField(populate_from='name', unique=True)
    seo_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    page_password = models.CharField(max_length=255, blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    view_count = models.IntegerField(default=0, blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    # Featured Image and ID
    featured_image = models.URLField(blank=True, null=True, help_text="URL of the featured image")
    image_id = models.CharField(max_length=255, blank=True, null=True, help_text="Optional image ID for tracking")

    class Meta:
        abstract = True

    def __str__(self):
        return self.name or "Untitled Page"


# Page Model (general static pages)
class Page(BasePage):
    pass


# Post Model (e.g., blog posts)
class Post(BasePage):
    excerpt = models.TextField(blank=True, null=True)
    allow_comments = models.BooleanField(default=True)
    categories = models.ManyToManyField(Category, blank=True, related_name="posts")
    tags = TaggableManager(blank=True)


# Product Model (e.g., e-commerce products)
class Product(BasePage):
    excerpt = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_quantity = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True)
    categories = models.ManyToManyField(ProductCategory, blank=True, related_name="products")


# Service Model (e.g., service offerings)
class Service(BasePage):
    excerpt = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    categories = models.ManyToManyField(ServiceCategory, blank=True, related_name="services")
