from django.urls import path
from . import views

from .views import SignupView, LoginView, recommended_treks_api


    


urlpatterns = [

    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),

    path('users/', views.UserProfileListCreateView.as_view()),
    path('users/<int:id>/', views.UserProfileDetailView.as_view()),

    path('treks/', views.TrekListCreateView.as_view()),
    path('treks/<int:id>/', views.TrekDetailView.as_view()),

    path('tims/', views.TimsApplicationListCreateView.as_view()),
    path('tims/<int:id>/', views.TimsApplicationDetailView.as_view()),

    path('posts/', views.PostListCreateView.as_view()),
    path('posts/<int:pk>/', views.PostDetailView.as_view()),

    path('comments/', views.CommentListCreateView.as_view()),
    path('comments/<int:pk>/', views.CommentDetailView.as_view()),

    path('likes/', views.LikeListCreateView.as_view()),
    path('likes/<int:pk>/', views.LikeDetailView.as_view()),

    path('favorites/', views.FavoriteListCreateView.as_view()),
    path('favorites/<int:pk>/', views.FavoriteDetailView.as_view()),

    path('interactions/', views.UserTrekInteractionView.as_view()),

    path('transit-pass/', views.TransitPassListCreateView.as_view()),
    path('transit-pass/<int:pk>/', views.TransitPassDetailView.as_view()),

    path('recommendations/', recommended_treks_api),
]
