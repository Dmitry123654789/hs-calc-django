from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path(
        "register/",
        views.RegisterView.as_view(),
        name="register",
    ),
    path(
        "password-change/",
        views.PasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password-change/done/",
        views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path(
        "admin/users/",
        views.AdminUserListView.as_view(),
        name="admin_user_list",
    ),
    path(
        "admin/users/<int:pk>/",
        views.AdminUserDetailView.as_view(),
        name="admin_user_detail",
    ),
    path(
        "admin/users/<int:pk>/delete/",
        views.AdminUserDeleteView.as_view(),
        name="admin_user_delete",
    ),
    path(
        "api/buyers/",
        views.BuyerListView.as_view(),
        name="api_buyers_list",
    ),
    path("buyers/", views.BuyerListCreateView.as_view(), name="buyers_list"),
    path(
        "buyers/<int:pk>/",
        views.BuyerDetailView.as_view(),
        name="buyer_detail",
    ),
    path(
        "buyers/<int:pk>/delete/",
        views.BuyerDeleteView.as_view(),
        name="buyer_delete",
    ),
]
