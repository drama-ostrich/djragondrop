from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.apps import apps
from django.http import JsonResponse, HttpResponse, Http404
from braces.views import SuperuserRequiredMixin

from django.forms import modelform_factory, widgets

from django.conf import settings

from codex.models import *

# IDEAS FOR SETTINGS
#
# model_url_kwarg
# related_property_name
DJRAGON_DONT_WRITE_TO_DATABASE = getattr(settings, "DJRAGON_DONT_WRITE_TO_DATABASE", False)
DJRAGON_FORCE_MANY_TO_ONE = getattr(settings, "DJRAGON_FORCE_MANY_TO_ONE", True)  # ha, dragonforce.
DJRAGON_ALLOWED_MODELS = ['Course', 'Module', 'Lesson', 'Activity', 'Toolkit', 'ToolkitSet', 'ToolkitTool']
DJRAGON_MODEL_FORM_FIELDS = {
    'Course': ('course_title', 'is_active'),
    'Module': ('module_title', 'is_active'),
    'Lesson': ('lesson_title', 'is_active'),
    'Activity': ('activity_title', 'is_active'),
}
DJRAGON_EXCLUDED_FIELDS = ('created_by', 'edited_by', 'created_date', 'last_update')


class ModelFromUrlMixin(object):
    model_url_kwarg = 'model'
    app_label = 'codex'
    model_name = None
    excluded_fields = DJRAGON_EXCLUDED_FIELDS
    model = None
    success_url = '/'
    allowed_models = DJRAGON_ALLOWED_MODELS
    model_form_fields = DJRAGON_MODEL_FORM_FIELDS

    def get_model_from_url(self, **kwargs):
        self.model_name = self.kwargs.get(self.model_url_kwarg, None)
        if self.model_name in self.allowed_models:
            self.model = apps.get_model(app_label=self.app_label, model_name=self.model_name)
        else:
            self.model = None

    def get_child_model(self):
        try:
            self.parent_pk = self.kwargs.get('pk', None)
            self.parent = self.model.objects.get(guid=self.parent_pk)
            self.child_model = self.parent.children.model
            self.child_model_name = self.child_model.__name__
        except AttributeError:
            self.child_model = None
            self.child_model_name = None

        if self.child_model and hasattr(self.model.children, 'through'):
            self.through_model = self.model.children.through
        else:
            self.through_model = None

    def get(self, request, *args, **kwargs):
        if self.model == None:
            self.get_model_from_url(**kwargs)

            if self.model == None: # If model is still None, we didn't find a model or it wasn't allowed
                raise Http404('Model not found or not allowed')

        return super(ModelFromUrlMixin, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.model is None:
            self.get_model_from_url(**kwargs)
        if hasattr(self, 'form_class') and self.form_class is None:
            self.form_class = self.form_class_from_model()
        response = super(ModelFromUrlMixin, self).post(request, *args, **kwargs)
        return HttpResponse(status=201)  # created

    def get_context_data(self, **kwargs):
        context = super(ModelFromUrlMixin, self).get_context_data(**kwargs)
        context['model_name'] = self.model_name
        context = self.add_form_to_context(context)
        return context

    def form_class_from_model(self):
        if self.model_name in self.model_form_fields:
            Form = modelform_factory(self.model, fields=self.model_form_fields[self.model_name], widgets={'user': widgets.TextInput})
        else:
            Form = modelform_factory(self.model, exclude=self.excluded_fields, widgets={'user': widgets.TextInput})
        return Form

    def add_form_to_context(self, context):
        Form = self.form_class_from_model()
        context['form'] = Form()
        return context


class SecurityMixin(object):
    def get_queryset(self):
        qs = super(SecurityMixin, self).get_queryset()
        if hasattr(self.model, 'user'):
            user = self.request.user.codesters_user.first()
            qs = qs.filter(user=user)
        return qs


class DjragonListView(ModelFromUrlMixin, ListView):
    related_children_name = 'children'
    related_parent_name = 'parents'
    model = None

    def get_context_data(self, **kwargs):
        context = super(DjragonListView, self).get_context_data(**kwargs)

        # Here's a hack:
        # to get the parent and child model we need a reference object
        # just steal the first object from our queryset
        obj = self.object_list.first()

        # get parents info
        if hasattr(obj, self.related_parent_name):
            qs = getattr(obj, self.related_parent_name)
            context['parent_model_name'] = qs.model.__name__
            context['parent_model_pk'] = self.request.GET.get('parent_pk')

        # get children info
        print 'child model name'
        if hasattr(obj, self.related_children_name):
            qs = getattr(obj, self.related_children_name)
            context['child_model_name'] = qs.model.__name__

        context['model_name'] = self.model.__name__
        context = self.add_form_to_context(context)
        return context


class ModelList(SuperuserRequiredMixin, SecurityMixin, DjragonListView):
    template_name = 'djragon/main.html'
    paginate_by = 100


class ModelListAjax(SuperuserRequiredMixin, SecurityMixin, DjragonListView):
    template_name = 'djragon/partial/one_list.html'
    model = None
    '''
    parent model pk posted in querystring
    '''
    def post(self, request, *args, **kwargs):

        self.model_name = self.kwargs.get(self.model_url_kwarg, None)
        self.model = apps.get_model(app_label=self.app_label, model_name=self.model_name)

        # This should be something like:
        # objects = request.POST.getlist('items[]')
        # but I couldn't get that to work
        # I think jquery ui is posting data in a bad format
        # so parse it ourselves I guess
        pk_list = request.POST.get('items[]').replace('item[]=', '').split('&')

        objects = list(self.model.objects.filter(pk__in=pk_list))

        json = {'result': 'success'}
        for i, pk in enumerate(pk_list):
            for obj in objects:
                if pk == obj.pk:
                    try:
                        original_position = obj.position
                        obj.position = i
                        if not DJRAGON_DONT_WRITE_TO_DATABASE:
                            obj.save()
                    except Exception:
                        json = {'result': 'Model must have a "position" property to allow ordering'}

        return JsonResponse(json)

    def get_queryset(self):

        # Hack: get a random object from this model, get the parents model,
        # use that to query for the parent, use that to query children to get
        # the list we want

        # the alternative is just to use a DetailView to get the parent model and object
        # then just use the children from that object

        # I decided to do this because the "model" of this view should be the list we display
        # then the other forms and things associated with this view will correspond with the model.

        parent_pk = self.request.GET.get('parent_pk')

        random_object = self.model.objects.first()
        ParentModel = random_object.parents.model
        parent = ParentModel.objects.get(pk=parent_pk)
        qs = parent.children

        return qs


class RelateChild(SuperuserRequiredMixin, ModelFromUrlMixin, View):

    def post(self, request, *args, **kwargs):

        self.get_model_from_url(**kwargs)
        self.get_child_model()

        child_pk = self.kwargs.get('child_pk', None)
        new_child = self.child_model.objects.get(guid=child_pk)


        #
        # Depending on options, we can either add to the many to many
        # or force only one to many (even if the relationship is many to many in the model file)
        #

        if self.through_model:  # is this a many to many with a through?

            RelationshipModel = self.through_model

            if DJRAGON_FORCE_MANY_TO_ONE and not DJRAGON_DONT_WRITE_TO_DATABASE:
                # I would rather get the relationship object already related to this
                # child, and just reassign it to the parent, but I can't find a way to query
                # to the relationship model
                # So just remove all parents from the child
                new_child.parents.clear()  # This deletes all relationships to all parents.

            new_relationship = RelationshipModel()
            new_relationship.parent = self.parent
            new_relationship.child = new_child
            if not DJRAGON_DONT_WRITE_TO_DATABASE:
                new_relationship.save()
        else:
            new_child.parents = self.parent
            if not DJRAGON_DONT_WRITE_TO_DATABASE:
                new_child.save()



        json = {'result': 'success'}
        return JsonResponse(json)


class CreateChild(SuperuserRequiredMixin, ModelFromUrlMixin, CreateView):

    success_url = '/'

    def post(self, request, *args, **kwargs):

        self.get_model_from_url(**kwargs)
        self.get_child_model()

        # to use the django CreateView, we need self.model to be the model thats created
        self.parent_model = self.model
        self.model = self.child_model

        self.form_class = self.form_class_from_model()
        form = self.get_form()
        if form.is_valid():
            print 'form valid'
            response_redirect = self.form_valid(form)  # now self.object is saved
        else:
            print 'form invalid'
            response_redirect = self.form_invalid(form)

        if hasattr(self, 'object') and self.object:  # if we created something, make a relationship

            if self.through_model:
                new_relationshp = self.through_model.create()
                new_relationshp.parent = self.parent
                new_relationshp.child = self.object
                new_relationshp.save()
            else:
                self.object.parent = self.parent
                self.object.save()
            return HttpResponse(status=201)  # created

        return HttpResponse('Object was not created.', status=503)  # unavailable


class C(SuperuserRequiredMixin, ModelFromUrlMixin, CreateView):

    # Security, users can only make objects for themselves
    def form_valid(self, form):
        if hasattr(form.fields, 'user'):
            print 'user value:'
            print form.fields['user'].value
            form.fields['user'].value = self.request.user.codesters_user.pk
        return super(C, self).form_valid(form)


class R(ModelFromUrlMixin, DetailView):
    pass


class U(ModelFromUrlMixin, UpdateView):
    pass


class D(ModelFromUrlMixin, DeleteView):
    pass

