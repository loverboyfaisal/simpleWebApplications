from flask import Flask,render_template
from .dashboard import dashboard
from .items import items
from .mod import create_database,create_inventory_table,create_history_table,create_sales_table,ensure_column,ensure_saled_status,ensure_saled_in_history
from .status_names import label_status
def create_app():
    create_database()
    create_inventory_table()
    create_history_table()
    create_sales_table()
    # migrate tables created before the size/color columns existed
    ensure_column("inventory","product_size","enum('s','m','l','xl','xxl')")
    ensure_column("status_history","product_color","varchar(255)")
    ensure_column("status_history","product_size","varchar(10)")
    ensure_saled_status()
    ensure_saled_in_history()
    app = Flask(__name__)
    app.secret_key="KEY_SEC"
    app.register_blueprint(items,url_prefix='/')
    app.register_blueprint(dashboard,url_prefix='/')

    @app.route('/')
    def home():
        return render_template("home.html")

    @app.context_processor
    def inject_status_names():
        return {"label_status": label_status}

    return app