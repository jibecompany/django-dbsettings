from functools import update_wrapper
from django.conf.urls import patterns, url
from django.contrib import admin

from .models import Setting
from .views import site_settings, app_settings

class SettingAdmin(admin.ModelAdmin):
    """Register the settings views under admin, so we don't need to
    add it to urls ourselves, and we have a link for our users in the
    Django admin.
    """
    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name

        urlpatterns = patterns('',
            url(r'^$', wrap(site_settings), name='%s_%s_changelist' % info),
            url(r'^(?P<app_label>[^/]+)/$', wrap(app_settings)),
        )
        return urlpatterns

admin.site.register(Setting, SettingAdmin)
  