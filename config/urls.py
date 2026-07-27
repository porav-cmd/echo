from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.views import home_view, login_view, logout_view, web_register_view, new_chat_view

urlpatterns = [
    # Full-Stack Web App UI
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('web-register/', web_register_view, name='web_register'),
    path('new-chat/', new_chat_view, name='new_chat'),

    # Admin Portal
    path('admin/', admin.site.urls),

    # REST API v1 Endpoints
    path('api/v1/', include('api.urls')),

    # JWT Authentication Endpoints
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Static Assets Serving for Development
if settings.DEBUG:
    urlpatterns += static('/css/', document_root=settings.BASE_DIR / 'css')
    urlpatterns += static('/media/', document_root=settings.BASE_DIR / 'media')
