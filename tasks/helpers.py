from tasks.models import Transaction


class TransactionCreation:
    def create_transaction_success(self,
                                   task=None,
                                   author=None,
                                   price=None,
                                   executor=None):
        Transaction.objects.create(
            task=task,
            author=author,
            price=price,
            executor=executor,
            status='Success')

    def create_transaction_fail(self,
                                task=None,
                                author=None,
                                price=None,
                                executor=None):
        Transaction.objects.create(
            task=task,
            author=author,
            price=price,
            executor=executor,
            status='Fail')
