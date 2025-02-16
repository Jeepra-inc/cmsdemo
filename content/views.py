from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from .models import Page, Post, Service, Product
from .serializers import PageSerializer, PostSerializer, ServiceSerializer, ProductSerializer
from rest_framework.response import Response

class BaseContentView:
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

class ContentListCreateView(BaseContentView, generics.ListCreateAPIView):
    pass

class ContentDetailView(BaseContentView, generics.RetrieveUpdateDestroyAPIView):
    pass

class PageListCreateView(ContentListCreateView):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

class PageDetailView(ContentDetailView):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

class PostListCreateView(ContentListCreateView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class PostDetailView(ContentDetailView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class ServiceListCreateView(ContentListCreateView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

class ServiceDetailView(ContentDetailView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

class ProductListCreateView(ContentListCreateView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductDetailView(ContentDetailView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer