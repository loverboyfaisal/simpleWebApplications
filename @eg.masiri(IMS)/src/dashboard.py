from flask import Blueprint,render_template
from .mod import get_status_summary,get_available_variants,get_sold_variants,get_refunded_variants,get_refunded_items,get_sales,get_sales_summary

dashboard = Blueprint("dashboard",__name__)


@dashboard.route('/dashboard')
def show_dashboard():
    summary = get_status_summary()
    variants = get_available_variants()
    sold_variants = get_sold_variants()
    refunded_variants = get_refunded_variants()
    refunded_items = get_refunded_items()
    sold_total = sum(row[4] or 0 for row in sold_variants)
    refunded_total = sum(row[4] or 0 for row in refunded_variants)
    sales = get_sales()
    sales_count, sales_total = get_sales_summary()
    return render_template(
        "dashboard.html",
        summary=summary,
        variants=variants,
        sold_variants=sold_variants,
        refunded_variants=refunded_variants,
        sold_total=sold_total,
        refunded_total=refunded_total,
        refunded_items=refunded_items,
        sales=sales,
        sales_count=sales_count,
        sales_total=sales_total,
    )
