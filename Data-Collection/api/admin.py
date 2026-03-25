from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from .models import DataCollection

try:
    admin.site.unregister(Group)
except Exception:
    pass


@admin.register(DataCollection)
class DataCollectionAdmin(admin.ModelAdmin):
    list_display    = ('id', 'block', 'meters', 'original_name', 'created_at')
    list_filter     = ('block',)
    search_fields   = ('block', 'original_name')
    ordering        = ('-created_at',)
    readonly_fields = ('created_at',)


class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'is_active')
    fieldsets = (
        (None,      {'fields': ('email', 'password')}),
        ('Access',  {'fields': ('is_active',)}),
    )
    add_fieldsets = (
        (None, {
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    filter_horizontal = ()
    list_filter       = ('is_active',)
    ordering          = ('email',)

    def save_model(self, request, obj, form, change):
        obj.username     = obj.email
        obj.is_staff     = True
        obj.is_superuser = True
        super().save_model(request, obj, form, change)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)