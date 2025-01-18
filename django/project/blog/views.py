from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from .models import BlogPost
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import status


# Token 발행
class TokenObtainPairView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# Access Token 검증
class ProtectedView(APIView):
    def get(self, request):
        return Response({'message': 'Access Token is valid!'}, status=status.HTTP_200_OK)

# 로그인 사용자만 가능한 뷰
@login_required
def blog_list(request):
    posts = BlogPost.objects.all()
    return render(request, 'blog_list.html', {'posts': posts})

# 특정 권한 뷰
@permission_required('blog.add_blogpost', raise_exception=True)
def create_blog_post(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        # 현재 로그인한 사용자를 작성자로 설정
        author = request.user
        BlogPost.objects.create(title=title, content=content, author=author)
        return redirect('blog_list')  # 블로그 리스트 페이지로 리디렉션
    return render(request, 'create_blog_post.html')

# 수정 뷰
@permission_required('blog.change_blogpost', raise_exception=True)
def update_blog_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    if request.method == "POST":
        post.title = request.POST.get('title')
        post.content = request.POST.get('content')
        post.save()
        return redirect('blog_list')  # 수정 후 블로그 리스트로 리디렉션
    return render(request, 'update_blog_post.html', {'post': post})

# 삭제 뷰
@permission_required('blog.delete_blogpost', raise_exception=True)
def delete_blog_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    if request.method == "POST":
        post.delete()
        return redirect('blog_list')  # 블로그 리스트 페이지로 리디렉션
    return render(request, 'delete_blog_post.html', {'post': post})