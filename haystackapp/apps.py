from django.apps import AppConfig

class HaystackappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'haystackapp'

    def ready(self):
        from haystackapp.src.hs_pipe_init import initialize
        # This is where I will download transcripts and initialize the Haystack pipeline
        global hspipe 
        hspipe = initialize()