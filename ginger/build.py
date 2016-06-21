import hashlib
import os
import pathlib
import re
import shutil
import sys
import time

from csscompressor import compress
from jinja2 import Environment, FileSystemLoader
from jsmin import jsmin
import sass
import yaml

from .conf import args, settings

os.chdir(os.getcwd())
loader = FileSystemLoader(os.path.join(os.getcwd(),
                                       settings.input_dir,
                                       settings.templates_dir
                                       ))
env = Environment(loader=loader)


def make_path(parts):
    """
        If parts is an array join them with os.path.sep
        else return untouched
    """

    file_name = parts
    if isinstance(parts, list):
        file_name = os.path.sep.join(parts)

    return file_name


def save_to_output(content, file_name):
    """
        Save content to the given file.
        If file_name is an array, join it with os.path.sep
    """

    file_name = make_path(file_name)

    os.makedirs(
        os.path.dirname(
            os.path.join(settings.output_dir, file_name)
        ),
        exist_ok=True
    )

    with open(settings.output_dir + os.path.sep + file_name, "w") as f:
        f.write(content)

    return file_name


def save_compiled_css():

    # Compile our SASS
    css_in_fn = make_path([settings.input_dir,
                           settings.templates_dir,
                           settings.css_dir,
                           settings.css_input_file
                           ])
    sass_output = sass.compile(filename=css_in_fn)

    if not args.dev:
        sass_output = compress(sass_output)

    # generate a hash of the file
    css_hash = hashlib.sha1(sass_output.encode('utf-8')).hexdigest()

    # save the css file
    css_out_name = settings.css_output_file_mask.format(
        hash=css_hash[:settings.filename_hash_length])
    css_file_name = save_to_output(sass_output, [settings.css_dir, css_out_name])

    return '/' + css_file_name


def save_merged_js():

    # we'll maintain the original folder name as well as the file name
    js_files = {}

    js_dir = make_path([settings.input_dir,
                        settings.templates_dir,
                        settings.js_dir])

    for folder, sub_dirs, files in os.walk(js_dir):
        if files:
            js_folder_name = folder.rsplit('/', 1)[1]
            js = ''
            for js_file in files:
                with open(folder + os.path.sep + js_file) as file:
                    js += file.read()

            if not args.dev:
                js = jsmin(js)

            # generate a hash of the file
            js_hash = hashlib.sha1(js.encode('utf-8')).hexdigest()

            # generate name and save the file
            js_file_name = settings.js_output_file_mask.format(
                name=js_folder_name, hash=js_hash[:settings.filename_hash_length])
            js_files[js_folder_name] = save_to_output(js, [settings.js_dir, js_file_name])

    return js_files


def get_input_pages():

    pages = []

    content_dir = make_path([settings.input_dir, settings.content_dir])
    for folder, sub_dirs, files in os.walk(content_dir):
        for yaml_file in files:
            if os.path.isfile(folder + os.path.sep + yaml_file):
                with open(folder + os.path.sep + yaml_file) as file:
                    data = yaml.load(file)
                    pages.append(data)

    return pages


def delete_output_contents():
    for root, dirs, files in os.walk(settings.output_dir):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def copy_files():

    template_dir = make_path([settings.input_dir, settings.templates_dir])
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            for copy_re in settings.copy_unmodified:
                if re.match(copy_re, file):
                    p = pathlib.PurePosixPath(os.path.join(root, file))
                    input_filename = os.path.join(root, file)
                    output_filename = os.path.join(
                        settings.output_dir, str(p.relative_to(template_dir)))

                    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

                    shutil.copy(input_filename, output_filename)


def build():

    start_time = time.time()
    print("Rebuilding... ", end="")
    sys.stdout.flush()

    if not settings.preserve_output_on_rebuild:
        delete_output_contents()

    css_file_name = save_compiled_css()

    js_file_names = save_merged_js()

    pages = get_input_pages()
    pages_meta = [p.get('meta', {}) for p in pages]

    for page in pages:

        meta = page.get('meta', {})
        context = page.get('context', {})

        context.update({
            'css_file_name': css_file_name,
            'js_file_names': js_file_names,
            'pages': pages_meta,
            'meta': meta
        })

        template = env.get_template(meta.get('template', settings.default_template))
        output = template.render(**context)

        filename = meta.get('save_as', 'missing_save_as.html')
        save_to_output(output, filename)

    copy_files()

    time_taken = (time.time() - start_time) * 1000
    print("Done, took {ms}ms".format(ms=time_taken))
