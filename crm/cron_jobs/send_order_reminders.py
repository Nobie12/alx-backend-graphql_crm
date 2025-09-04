from datetime import timedelta
from django.utils import timezone
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
client = Client(transport=transport, fetch_schema_from_transport=True)
query = gql(
    """
    query {
        orders(orderDate_Gte: $last_seventh_day) {
            id
            customer {
                email
            }
        }
    }"""
)
last_seventh_day = timezone.now() - timedelta(days=7)
query.variables = {"last_seventh_day": last_seventh_day}

result = client.execute(query)

with open("/tmp/order_reminders_log.txt", "a") as f:
    for order in result["orders"]:
        f.write(f"{order['id']}, {order['customer']['email']}, {timezone.now()}\n")

print("Order reminders processed!")