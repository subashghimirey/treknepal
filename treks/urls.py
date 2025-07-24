from django.urls import path
from . import views

from .views import AuthViewSet, TIMSViewSet, TrekViewSet, PostViewSet, LikeViewSet, CommentViewSet, FavoriteViewSet, SOSAlertViewSet, VerificationViewSet, RecommendationViewSet

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
router.register(r'recommendations', RecommendationViewSet, basename='recommendation')

urlpatterns = [
   
    path('users/', views.UserProfileListCreateView.as_view()),
    path('users/<int:id>/', views.UserProfileDetailView.as_view()),

    path('interactions/', views.UserTrekInteractionView.as_view()),

]


urlpatterns += router.urls