# Импортируем из приложения django.contrib.auth нужный view-класс
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('logout/',
         # Прямо в описании обработчика укажем шаблон,
         # который должен применяться для отображения возвращаемой страницы.
         LogoutView.as_view(template_name='users/logged_out.html'),
         name='logout'
         ),
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('login/', LoginView.as_view(template_name='users/login.html'),
         name='login'),
]
