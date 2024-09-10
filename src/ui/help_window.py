# *******************************************************
# * Copyright (c) 2022-2024 CAST.  All rights reserved. *
# *******************************************************

import markdown
from src.ui.constants import *
from gi.repository import Gtk, WebKit2


# FIXME: There seems to be an issue with displaying an image.
#  Additionally, a fragment of C code is not being displayed correctly.

class HelpWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="About ASMGraph",
                         default_width=HELP_WINDOW_WIDTH,
                         default_height=HELP_WINDOW_HEIGHT)

        with open(os.path.join(ROOT_DIR, README)) as readme_file:
            markdown_text = readme_file.read()

        html_content = markdown.markdown(markdown_text)

        webview = WebKit2.WebView()
        webview.load_html(html_content, DUMMY_BASE_URL)

        self.add(webview)
