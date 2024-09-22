from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.generic import ListView, DetailView
from django.core.mail import send_mail
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from .models import Blog, Comment
from .forms import CommentForm


# Home view that requires login
@login_required
def home_view(request):
    user = request.user
    blogs = Blog.objects.all().order_by(
        "-published_date"
    )  # Fetch all blogs, order by published date (most recent first)
    paginator = Paginator(blogs, 5)  # Show 5 blogs per page

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "home.html", {"page_obj": page_obj, "user": user})


# Logout view
def logout_view(request):
    logout(request)
    return redirect("login")


# Signup view
def signup(request):
    if request.method == "POST":
        name = request.POST["name"]
        email = request.POST["email"].lower()
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]
        username = name

        if password != confirm_password:
            return render(request, "signup.html", {"error": "Passwords do not match"})

        if User.objects.filter(email=email).exists():
            return render(request, "signup.html", {"error": "Email already exists"})

        # Create user with the email as the username
        user = User.objects.create_user(
            username=username, email=email, password=password, first_name=name
        )
        user.save()
        return redirect("login")

    return render(request, "signup.html")


# Login view
def login_view(request):
    if request.method == "POST":
        email = request.POST["email"].lower()
        password = request.POST["password"]

        try:
            # Try to fetch the user by email to get the username for authentication
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            print("user doesnot exit")
            return render(request, "login.html", {"error": "Invalid email or password"})

        # Authenticate using username (email) and password
        user = authenticate(request, username=user.username, password=password)
        if user:
            print("User authenticated:", user.username)
        else:
            print("Authentication failed")
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            return render(request, "login.html", {"error": "Invalid email or password"})

    return render(request, "login.html")


# BlogList
class BlogListView(ListView):
    model = Blog
    template_name = "blog_list.html"
    context_object_name = "posts"
    paginate_by = 5  # Pagination


# BlogDetail
class BlogDetailView(DetailView):
    model = Blog
    template_name = "blog_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm()
        return context

    def post(self, request, *args, **kwargs):
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = self.get_object()
            comment.user = request.user
            comment.save()
            return redirect(self.get_object().get_absolute_url())


# BlogSearch
def blog_search(request):
    query = request.GET.get("q")
    if query:
        posts = (
            Blog.objects.filter(
                Q(title__icontains=query)
                | Q(content__icontains=query)
                | Q(tags__name__icontains=query)
            )
            .annotate(
                score=Count("title", filter=Q(title__icontains=query)) * 2
                + Count("content", filter=Q(content__icontains=query))
                + Count("tags", filter=Q(tags__name__icontains=query))
            )
            .order_by("-score")
            .distinct()
        )
        print(posts)
    else:
        posts = Blog.objects.all()
    return render(request, "blog_list.html", {"posts": posts})


# Share Blog
def share_blog(request, blog_id):
    post = get_object_or_404(Blog, id=blog_id)

    if request.method == "POST":
        email = request.POST.get("email")
        print(email)
        try:
            send_mail(
                subject=f"Check out this blog post: {post.title}",
                message=f"Read the blog post here: {request.build_absolute_uri(post.get_absolute_url())}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            # messages.success(request, f"Blog post successfully shared with {email}")
        except Exception as e:

            messages.error(request, f"Failed to send email: {str(e)}")

        return redirect(post.get_absolute_url())

    return render(request, "share.html", {"post": post})


# Blog Like
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True
    return JsonResponse({"liked": liked, "likes_count": comment.likes.count()})
