from django.urls import path
from . import views

urlpatterns = [
    path("home/", views.home_view, name="home"),
    path("logout/", views.logout_view, name="logout"),
    path(
        "",
        views.login_view,
        name="login",
    ),
    path("signup/", views.signup, name="signup"),
    path("bloglist/", views.BlogListView.as_view(), name="blog_list"),
    path("post/<slug:slug>/", views.BlogDetailView.as_view(), name="blog_detail"),
    path("search/", views.blog_search, name="blog_search"),
    path("blog/share/<int:blog_id>/", views.share_blog, name="share_blog"),
    path("comment/<int:comment_id>/like/", views.like_comment, name="like_comment"),
]
