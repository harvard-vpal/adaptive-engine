from django.apps import apps

def reset_database(app='engine'):
        for model in apps.all_models[app].values():
            model.objects.all().delete()
