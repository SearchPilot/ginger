Ginger Static Site Generator
============================

Ginger is a very lightweight static site generator based on the [jinja template language](http://jinja.pocoo.org/). 

Unlike most static site generators Ginger is designed to work best for sites that are made up from a collection of pages. Ginger does not have the concept of blog posts, tags, categories, authors. If you need something more complicated then [Pelican](http://blog.getpelican.com/) is an obvious next step. 

Documentation is very lacking at the moment. This is something I hope to rectify soon.


Installation
------------

```
pip install ginger
```

Initial Setup
---------------

- mkdir `root_dir`
- mkdir `root_dir/input`
- mkdir `root_dir/input/templates`
- mkdir `root_dir/input/templates/styles`
- mkdir `root_dir/input/templates/scripts`
- mkdir `root_dir/output`

Then create ginger.yml with the following settings

```
---

    # the yml files for each page. relative to input_dir
    content_dir: pages

    # the directory holding the uncompiled css (relative to templates_dir)
    css_dir: styles

    # the file name of the parent scss file
    css_input_file: main.scss

    # the output file name mask (can use {hash}) to get unique filename based on the contents
    css_output_file_mask: styles.{hash}.css

    # files to copy unmodified from input_dir -> output_dir
    # relative path from templates will remain untouched
    # e.g. template/input/folder/123.png -> output/folder/123.png
    copy_unmodified: ['.*\.(gif|jpg|jpeg|png|ico|mp4)']

    # the default jinja template to use if not specified in the yml
    default_template: page.html

    # the directory holding the javascript.
    # js files will get concatenated into a single file named after the folder
    # e.g. vendor/a.js and vendor/b.js -> vendor.js
    js_dir: scripts

    # The format to name the javascript. Can use {name} and {hash}
    js_output_file_mask: "{name}.{hash}.js"

    # length of the hash to include in the filename
    filename_hash_length: 8

    # the directory holding all our template and content files
    input_dir: input

    # where should we save the resulting html
    output_dir: output

    # Should we keep the contents of the output directory each time we rebuild?
    preserve_output_on_rebuild: False

    # where can we find the templates (relative to input_dir)
    templates_dir: templates
```

During development run

```
ginger --dev --watch
```

The `--dev` or `-d` flag means that the css and js files aren't minified. This is both for speed reasons and to ease viewing the source code whilst developing. The `--watch` (or `w`) flag will watch the input folder for changes and recreate your output folder.


Finally run

```
ginger
```

Which rebuilds the output minifying the css and js
