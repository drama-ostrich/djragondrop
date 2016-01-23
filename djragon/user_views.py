from django.forms import ModelForm
from codex.models import Course, Module, Lesson, Activity
# Forms


class ModuleForm(ModelForm):
    class Meta:
        model = Module
        fields = ['is_active', 'module_title']