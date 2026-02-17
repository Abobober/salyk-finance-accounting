from django.urls import path
from .views import GetTelegramLinkView, BotLinkConfirmView, BotAuthView

urlpatterns = [
    path('link-token/', GetTelegramLinkView.as_view(), name='tg-get-link'),
    
    path('bot/link/', BotLinkConfirmView.as_view(), name='tg-bot-link'),
    path('bot/auth/', BotAuthView.as_view(), name='tg-bot-auth'),
]
