class DomainException(Exception):
    pass


class BusinessRuleException(DomainException):
    code = "BUSINESS_RULE_ERROR"


class FinePaymentRequiredException(BusinessRuleException):
    code = "FINE_PAYMENT_REQUIRED"

    def __init__(self):
        super().__init__(
            "A multa do empréstimo deve ser paga antes de devolver o livro"
        )


class NotFoundException(DomainException):
    pass


class UnauthorizedException(DomainException):
    pass
