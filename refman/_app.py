from flask import Flask, render_template
from flask.helpers import get_root_path
import pandas as pd
import numpy as np


def init_flask_app(references: pd.DataFrame):
    app = Flask("refman")

    @app.route('/')
    def index():
        return render_template(
            "index.html",
            data=references.to_html(table_id="references", classes="table table-striped table-hover")
        )

    return app


if __name__ == "__main__":
    app = init_flask_app(references=pd.DataFrame(np.random.randn(20, 5)))
    app.run(debug=True)
