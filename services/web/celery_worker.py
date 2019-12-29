import os
from field_capture import celery, create_app
app = create_app()
app.app_context().push()
