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


def save_to_output(content, file_name):
    """Save content to a file called file_name in output_dir"""

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
    """Compile and optionally minify source sass files

    Compile the file found at settings.css_input_file

    If we are not in dev mode also minify the file prior to saving.

    The output of the compilation is hashed prior to the file
    being saved with a name based on settings.css_output_file_mask

    Return the path of the saved file
    """

    # Compile our SASS
    css_in_fn = os.path.join(settings.input_dir,
                             settings.templates_dir,
                             settings.css_dir,
                             settings.css_input_file
                             )
    sass_output = sass.compile(filename=css_in_fn)

    if not args.dev:
        sass_output = compress(sass_output)

    # generate a hash of the file
    css_hash = hashlib.sha1(sass_output.encode('utf-8')).hexdigest()

    # save the css file
    css_out_name = settings.css_output_file_mask.format(
        hash=css_hash[:settings.filename_hash_length])
    css_file_name = save_to_output(sass_output, os.path.join(settings.css_dir,
                                                             css_out_name))

    return '/' + css_file_name


def save_merged_js():
    """Concatenate and optionally minify source javascript files

    For each directory in the settings.js_dir create a file
    named after the directory containing all js files
    concatenated together.

    If we are not in dev mode also minify the files.

    Each file is hashed, before saving and the hash can
    form part of the filename based on the settings.

    Each files is then saved to the output directory.

    return a dictionary keyed by the folder name holding the
    path to the js file.js_output_file_mask format mask

    Example:
    Given the following directory structure:
        - input/templates/js_dir/vendor/a.js
        - input/templates/js_dir/vendor/b.js
        - input/templates/js_dir/vendor/c.js
        - input/templates/js_dir/main/d.js

        (with js_output_file_mask={name}.{hash}.js)

    This will create:
        - output/js_dir/vendor.filehash.js (containing a.js, b.js and c.js)
        - output/js_dir/main.filehash.js (containing d.js)

    Returning:
    {
        'vendor': '/js_dir/vendor.filehash.js',
        'main': '/js_dir/main.filehash.js'
    }
    """

    js_files = {}
    js_dir = os.path.join(settings.input_dir,
                          settings.templates_dir,
                          settings.js_dir)

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
            js_files[js_folder_name] = '/' + save_to_output(
                js, os.path.join(settings.js_dir, js_file_name))

    return js_files


def get_input_pages():
    """Get a list of input pages defined by yml files

    Gather pages from settings.input_dir/settings.content_dir
    return the page variables defined in the source yml
    """

    pages = []

    content_dir = os.path.join(settings.input_dir, settings.content_dir)
    for folder, sub_dirs, files in os.walk(content_dir):
        for yaml_file in files:
            if os.path.isfile(folder + os.path.sep + yaml_file):
                with open(folder + os.path.sep + yaml_file) as file:
                    data = yaml.load(file)
                    pages.append(data)

    return pages


def delete_output_contents():
    """Delete all files and directories in settings.output_dir"""
    for root, dirs, files in os.walk(settings.output_dir):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def copy_files():
    """Copy files from input to output.

    Copy any files that match settings.copy_unmodified
    Copy from settings.input_dir/settings.template_dir
        to  settings.output_dir retaining the reletive path
    """

    template_dir = os.path.join(settings.input_dir, settings.templates_dir)
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


def generate_html(css_file_name, js_file_names):
    """Generate html files from the input yml

    Save a html file in the output folder for every input page.
    Each template is given:
        any variable defined in context from its source yml
        `css_file_name` - the path to the generated css
        `js_file_names` - a dictory holding
            source_folder_name: path to generated js
        `pages` - a list holding the meta info of all pages
        `meta` - the meta information of the current page
    """

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


def build():
    """Rebuild all html.

    build is called every time `ginger` is called from the command line.
    build is called when `ginger` is watch the input directory and
    sees a modification.

    build will:
    Optionally delete the output folder
    Compile and optionally minify the css file
    Concatenate and optionally minify any js files
    Rebuild all html from the templates / yml input
    """

    start_time = time.time()
    print("Rebuilding... ", end="")
    sys.stdout.flush()

    if not settings.preserve_output_on_rebuild:
        delete_output_contents()

    css_file_name = save_compiled_css()

    js_file_names = save_merged_js()

    generate_html(css_file_name, js_file_names)

    copy_files()

    time_taken = (time.time() - start_time) * 1000
    print("Done, took {ms}ms".format(ms=time_taken))
