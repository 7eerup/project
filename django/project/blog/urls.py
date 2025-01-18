from django.urls import path
from . import views
from .views import TokenObtainPairView, ProtectedView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('blogs/', views.blog_list, name='blog_list'),  # 블로그 게시물
    path('blogs/create/', views.create_blog_post, name='create_blog_post'), # 블로그 등록
    path('blogs/update/<int:post_id>/', views.update_blog_post, name='update_blog_post'),  # 블로그 수정
    path('blogs/delete/<int:post_id>/', views.delete_blog_post, name='delete_blog_post'),  # 블로그 삭제

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # 토큰 발행
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # 리프레시 토큰 사용
    path('api/protected/', ProtectedView.as_view(), name='protected_view'),  # Access Token 검증
]
