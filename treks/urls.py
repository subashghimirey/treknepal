from django.urls import path
from . import views

from .views import SignupView, LoginView, recommended_treks_api, TIMSViewSet

from rest_framework.routers import DefaultRouter
    
router = DefaultRouter()
router.register(r'tims', TIMSViewSet, basename='tims')

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),

    path('users/', views.UserProfileListCreateView.as_view()),
    path('users/<int:id>/', views.UserProfileDetailView.as_view()),

    path('treks/', views.TrekListCreateView.as_view()),
    path('treks/<int:id>/', views.TrekDetailView.as_view()),

    path('posts/', views.PostListCreateView.as_view()),
    path('posts/<int:pk>/', views.PostDetailView.as_view()),

    path('comments/', views.CommentListCreateView.as_view()),
    path('comments/<int:pk>/', views.CommentDetailView.as_view()),

    path('likes/', views.LikeListCreateView.as_view()),
    path('likes/<int:pk>/', views.LikeDetailView.as_view()),

    path('favorites/', views.FavoriteListCreateView.as_view()),
    path('favorites/<int:pk>/', views.FavoriteDetailView.as_view()),

    path('interactions/', views.UserTrekInteractionView.as_view()),

  
    path('recommendations/', recommended_treks_api),

    # path('send-sos/', views.send_sos, name='send_sos'),


    path('sos-alert/', views.send_sos_alert, name='send-sos-alert'),
    path('sos-alerts/', views.get_sos_alerts, name='get-sos-alerts'),
    path('sos-alerts/<int:alert_id>/', views.sos_alert_detail, name='sos-alert-detail'),
    path('sos-alerts/<int:alert_id>/resolve/', views.resolve_sos_alert, name='resolve-sos-alert'),

    path('verify-qr/', views.verify_qr_code, name='verify-qr'),
    path('check-role/', views.check_user_role, name='check-user-role'),
]


urlpatterns += router.urls