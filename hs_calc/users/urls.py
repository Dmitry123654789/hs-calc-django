__all__ = ()

import django.urls

from users import views

app_name = "users"

urlpatterns = [
    django.urls.path("login/", views.LoginView.as_view(), name="login"),
    django.urls.path("logout/", views.LogoutView.as_view(), name="logout"),
    django.urls.path("profile/", views.ProfileView.as_view(), name="profile"),
    django.urls.path(
        "register/",
        views.RegisterView.as_view(),
        name="register",
    ),
    django.urls.path(
        "password-change/",
        views.PasswordChangeView.as_view(),
        name="password_change",
    ),
    django.urls.path(
        "password-change/done/",
        views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    django.urls.path(
        "admin/users/",
        views.AdminUserListView.as_view(),
        name="admin_user_list",
    ),
    django.urls.path(
        "admin/users/<int:pk>/",
        views.AdminUserDetailView.as_view(),
        name="admin_user_detail",
    ),
    django.urls.path(
        "admin/users/<int:pk>/delete/",
        views.AdminUserDeleteView.as_view(),
        name="admin_user_delete",
    ),
    django.urls.path("api/buyers/", views.BuyerListView.as_view(), name="buyers_list"),
]
