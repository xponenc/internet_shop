from django.urls import path

from .views import product_detail, product_list, ProductListView, ProductDetailView, cart_view, add_to_cart, \
    remove_from_cart, ProductCreateView, ProductUpdateView, ProductDeleteView, ProductImageDeleteView, \
    CategoryCreateView, CategoryUpdateView, CategoryDeleteView, CategoryDetailView, CategoryListView, \
    ProductSetCategoryView, ProductJsonSearchView

app_name = "shop"

urlpatterns = [
    # path("products/<int:pk>", ProductDetailView.as_view(), name="product-detail"),
    path("products/<int:pk>", product_detail, name="product-detail"),
    # path("products/", ProductListView.as_view(), name="products"),
    path("products/", product_list, name="products"),
    path("products/create", ProductCreateView.as_view(), name="product-create"),
    path("products/<int:pk>/update", ProductUpdateView.as_view(), name="product-update"),
    path("products/<int:pk>/delete", ProductDeleteView.as_view(), name="product-delete"),
    path("products/product-image/<int:pk>/delete", ProductImageDeleteView.as_view(), name="product-image-delete"),
    path("product/<int:product_pk>/set-category/<int:category_pk>", ProductSetCategoryView.as_view(),
         name="product-set-category"),
    path("product/json-search", ProductJsonSearchView.as_view(),
         name="product-json-search"),

    path("category/", CategoryListView.as_view(), name="category-list"),
    path("category/<int:pk>", CategoryDetailView.as_view(), name="category-detail"),
    path("category/create", CategoryCreateView.as_view(), name="category-create"),
    path("category/<int:pk>/update", CategoryUpdateView.as_view(), name="category-update"),
    path("category/<int:pk>/delete", CategoryDeleteView.as_view(), name="category-delete"),

    path('cart/', cart_view, name='cart_view'),
    path('add-to-cart/<int:product_id>/<int:quantity>', add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
]
