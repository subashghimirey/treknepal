from django.urls import path
from . import views

from .views import AuthViewSet, recommended_treks_api, TIMSViewSet, TrekViewSet, PostViewSet, LikeViewSet, CommentViewSet, FavoriteViewSet, SOSAlertViewSet, VerificationViewSet

from rest_framework.routers import DefaultRouter
    
router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'tims', TIMSViewSet, basename='tims')
router.register(r'treks', TrekViewSet, basename='trek')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'likes', LikeViewSet, basename='like')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'sos', SOSAlertViewSet, basename='sos-alert')
router.register(r'verify', VerificationViewSet, basename='verify')

urlpatterns = [
   
    path('users/', views.UserProfileListCreateView.as_view()),
    path('users/<int:id>/', views.UserProfileDetailView.as_view()),

    path('interactions/', views.UserTrekInteractionView.as_view()),

  
    path('recommendations/', recommended_treks_api),
]


urlpatterns += router.urls