from . import celery_app
from datetime import datetime
import requests

graph_ql_endpoint = "http://localhost:8000/graphql"

@celery_app.task
def generate_crm_report():
    """
    Celery task that uses GraphQL endpoint to fetch:
      - total number of customers
      - total number of orders
      - total revenue (sum of product prices across all orders)
    Then logs the report to /tmp/crm_report_log.txt with a timestamp.
    """

    log_file = "/tmp/crm_report_log.txt"
    open_file_mode = "a"
    query = """
        query {
            customers
            orders {
                products
            }
        }
        """
    try:
        response = requests.post(
            graph_ql_endpoint,
            json={"query": query},
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"GraphQL request failed: {e}")
        return

    try:
        payload = response.json()
    except ValueError as e:
        print(f"Invalid JSON response: {e}")
        return

    if payload.get("errors"):
        print(f"GraphQL request failed: {payload['errors']}")
        return

    result = payload.get("data") or {}
    total_customers = len(result.get("customers") or [])
    orders = result.get("orders") or []
    total_revenue = 0.0

    for order in orders:
        for product in order.get("products") or []:
            total_revenue += product.get("price", 0.0)

    total_revenue = round(total_revenue, 2)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = f"{timestamp} Report: {total_customers} customers, {len(orders)} orders, {total_revenue} revenue."
    with open(log_file, open_file_mode) as f:
        f.write(f"{report}\n")