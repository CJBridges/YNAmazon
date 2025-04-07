from collections import namedtuple
from datetime import date

from amazonorders.entity.order import Order
from amazonorders.entity.transaction import Transaction
from amazonorders.orders import AmazonOrders
from amazonorders.session import AmazonSession
from amazonorders.transactions import AmazonTransactions

# import config
from settings import settings

TransactionWithOrderInfo = namedtuple(
    "TransactionWithOrderInfo",
    [
        "completed_date",
        "transaction_total",
        "order_total",
        "order_number",
        "order_link",
        "item_names",
    ],
)


def get_amazon_transactions() -> list[TransactionWithOrderInfo]:
    """Returns a list of transactions with order info.

    Returns:
        list[TransactionWithOrderInfo]: A list of transactions with order info
    """
    amazon_session = AmazonSession(
        username=settings.amazon_user,
        password=settings.amazon_password.get_secret_value(),
    )
    amazon_session.login()

    amazon_orders = AmazonOrders(amazon_session)
    orders: list[Order] = amazon_orders.get_order_history(
        year=str(date.today().year)
    )  # TODO - fetch previous year as well (and merge) if the current date is within the first month of this year
    orders.sort(key=lambda order: order.order_placed_date)
    orders_dict: dict[str, Order] = {order.order_number: order for order in orders}

    amazon_transactions: list[Transaction] = AmazonTransactions(
        amazon_session=amazon_session
    ).get_transactions(days=31)
    amazon_transactions.sort(key=lambda trans: trans.completed_date)

    amazon_transaction_with_order_details: list[TransactionWithOrderInfo] = []
    for transaction in amazon_transactions:
        if not (order := orders_dict.get(transaction.order_number)):
            continue
        amazon_transaction_with_order_details.append(
            TransactionWithOrderInfo(
                completed_date=transaction.completed_date,
                transaction_total=int(transaction.grand_total * -1000),
                order_total=int(order.grand_total * 1000),
                order_number=transaction.order_number,
                order_link=transaction.order_details_link,
                item_names=[item.title for item in order.items],
            )
        )

    return amazon_transaction_with_order_details


def print_amazon_transactions(
    amazon_transaction_with_order_details: list[TransactionWithOrderInfo],
):
    """Prints a list of transactions to the screen for inspection.

    Args:
        amazon_transaction_with_order_details (list[TransactionWithOrderInfo]): a list of transactions to print
    """
    for transaction in amazon_transaction_with_order_details:
        info = transaction._asdict()
        for label, value in info.items():
            if isinstance(value, list):
                print(f"{label}:")
                for i, item in enumerate(value, start=1):
                    print(f"    {i}: {item}")
            elif isinstance(value, int):
                print(f"{label}: ${value / 1000:.2f}")
            else:
                print(f"{label}: {value}")
        print()


if __name__ == "__main__":
    print_amazon_transactions(get_amazon_transactions())
