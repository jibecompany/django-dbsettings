from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

from dbsettings import loading, forms

import logging
log = logging.getLogger(__name__)

def staff_or_superuser(user):
    """
    :type user: django.contrib.auth.models.User
    """
    if user and user.is_active and (user.is_staff or user.is_superuser):
        return True
    return False

@user_passes_test(staff_or_superuser)
def app_settings(request, app_label, template='dbsettings/app_settings.html'):
    # Determine what set of settings this editor is used for
    if app_label is None:
        settings = loading.get_all_settings()
        title = _('Site settings')
    else:
        settings = loading.get_app_settings(app_label)
        title = _('%(app)s settings') % {'app': capfirst(app_label)}

    # Create an editor customized for the current user
    editor = forms.customized_editor(request.user, settings)

    if request.method == 'POST':
        # Populate the form with user-submitted data
        form = editor(request.POST.copy(), request.FILES)
        if form.is_valid():
            form.full_clean()

            n_changed = 0
            for name, value in form.cleaned_data.items():
                key = forms.RE_FIELD_NAME.match(name).groups()
                setting = loading.get_setting(*key)
                try:
                    storage = loading.get_setting_storage(*key)
                    current_value = setting.to_python(storage.value)
                except Exception, e:
                    log.info("An exception occurred trying to convert %s, "
                        "with value %s, to python.", name, value, exc_info=True)
                    current_value = None

                if current_value != setting.to_python(value):
                    args = key + (value,)
                    loading.set_setting_value(*args)

                    # Give user feedback as to which settings were changed
                    if setting.class_name:
                        location = setting.class_name
                    else:
                        location = setting.module_name
                    update_msg = (_(u'Updated %(desc)s on %(location)s') %
                                  {'desc': unicode(setting.description), 'location': location})
                    messages.add_message(request, messages.INFO, update_msg)
                    n_changed += 1

            if not n_changed:
                no_update_msg = (_(u'Nothing was changed'))
                messages.add_message(request, messages.INFO, no_update_msg)

            return HttpResponseRedirect(request.path)
    else:
        # Leave the form populated with current setting values
        form = editor()

    return render_to_response(template, {
        'title': title,
        'form': form,
    }, context_instance=RequestContext(request))


# Site-wide setting editor is identical, but without an app_label
def site_settings(request):
    return app_settings(request, app_label=None, template='dbsettings/site_settings.html')
# security is checked on app_settings
