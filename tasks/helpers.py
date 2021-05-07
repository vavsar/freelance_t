from tasks.models import Transaction


class TransactionCreation:
    def __init__(self, task, author, price, executor=None):
        self.task = task
        self.author = author
        self.price = price
        self.executor = executor

    def create_transaction_success(self, executor=None):
        Transaction.objects.create(
            task=self.task,
            author=self.task.author,
            price=self.task.price,
            executor=executor,
            status='Success')

    def create_transaction_fail(self, executor=None):
        Transaction.objects.create(
            task=self.task,
            author=self.task.author,
            price=self.task.price,
            executor=executor,
            status='Fail')
