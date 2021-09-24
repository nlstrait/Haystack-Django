from django.apps import AppConfig

class HaystackappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'haystackapp'

    def ready(self):
        from haystackapp.src.hs_pipe_init import initialize
        # This is where I will download transcripts and initialize the Haystack pipeline
        print('Initializing Haystack pipeline...')
        try:
            global hspipe 
            hspipe = initialize()
            print('Haystack pipline initialized.')
        except NotImplementedError as e:
            print(e)