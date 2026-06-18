import django.conf
import django.conf.urls.static
import django.contrib.admin
import django.urls

import about.urls
import calculate.urls
import orders.urls
import users.urls


urlpatterns = [
    django.urls.path("admin/", django.contrib.admin.site.urls),
    django.urls.path("auth/", django.urls.include(users.urls)),
    django.urls.path("calculator/", django.urls.include(calculate.urls)),
    django.urls.path("order/", django.urls.include(orders.urls)),
    django.urls.path("", django.urls.include(about.urls)),
]


if django.conf.settings.DEBUG:
    import debug_toolbar.toolbar

    urlpatterns += debug_toolbar.toolbar.debug_toolbar_urls()

    urlpatterns += django.conf.urls.static.static(
        django.conf.settings.STATIC_URL,
        document_root=django.conf.settings.STATIC_ROOT,
    )

    urlpatterns += django.conf.urls.static.static(
        django.conf.settings.MEDIA_URL,
        document_root=django.conf.settings.MEDIA_ROOT,
    )
