from django.contrib import admin
from .models import *

admin.site.register(UserProfile)
admin.site.register(Trek)
admin.site.register(TimsApplication)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Favorite)
admin.site.register(UserTrekInteraction)
admin.site.register(TransitPass)
admin.site.register(EmergencyContactPoint)
admin.site.register(SOSAlert)

