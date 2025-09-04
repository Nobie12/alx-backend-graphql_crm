from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

graph_ql_endpoint = "http://localhost:8000/graphql"
def log_crm_heartbeat():
    """
    logs (appends) a message in the format DD/MM/YYYY-HH:MM:SS CRM is alive to/tmp/crm_heartbeat_log.txt.
    also queries the GraphQL hello field to verify the endpoint is responsive.
    """
    log_file = "/tmp/crm_heartbeat_log.txt"
    open_file_mode = "a"

    with open(log_file, open_file_mode) as f:
        f.write(f"{datetime.now()}: CRM is alive.\n")

    # query hello
    transport = RequestsHTTPTransport(url=graph_ql_endpoint)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    query = gql(
        """
        query {
        hello
        }"""
    )
    result = client.execute(query)
    assert result["hello"] == "Hello stranger"

def update_low_stock():
    """
    executes the updateLowStockProducts mutation.
    then Logs updated product names and new stock levels to /tmp/low_stock_updates_log.txt with a timestamp.
    """
    log_file = "/tmp/low_stock_updates_log.txt"
    open_file_mode = "a"

    transport = RequestsHTTPTransport(url=graph_ql_endpoint)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    query = gql(
        """
        mutation {
            updateLowStockProducts(stockThreshold: $stock_threshold) {
                products {
                    name
                    stock
                }
            }
        }
        """
    )
    stock_threshold = 10
    query.variables = {"stock_threshold": stock_threshold}
    result = client.execute(query)

    with open(log_file, open_file_mode) as f:
        for product in result["updateLowStockProducts"]["products"]:
            f.write(f"{datetime.now()}: {product['name']} has {product['stock']} stock left.\n")
