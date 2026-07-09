from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin import site
from django.urls import include, path

import about.urls
import orders.urls
import users.urls


urlpatterns = [
    path("admin/", site.urls),
    path("auth/", include(users.urls)),
    path("order/", include(orders.urls)),
    path("", include(about.urls)),
]


if settings.DEBUG:
    import debug_toolbar.toolbar

    urlpatterns += debug_toolbar.toolbar.debug_toolbar_urls()

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
