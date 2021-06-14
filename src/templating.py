import os.path
import logging

from jinja2 import FileSystemLoader, Environment, exceptions

logger = logging.getLogger(__name__)

def render(charm_dir, source, context):
    """
    Render a template.

    The context should be a dict containing the values to be replaced in the
    template.
    """
    templates_dir = os.path.join(charm_dir, 'templates')
    template_env = Environment(loader=FileSystemLoader(templates_dir))

    try:
        template = template_env.get_template(source)
    except exceptions.TemplateNotFound as e:
        logger.error('Could not load template %s from %s.' %
                    (source, templates_dir))
        raise e
    return template.render(context)
