class DomainException(Exception):
    pass


class BusinessRuleException(DomainException):
    code = "BUSINESS_RULE_ERROR"


class FinePaymentRequiredException(BusinessRuleException):
    code = "FINE_PAYMENT_REQUIRED"

    def __init__(self):
        super().__init__(
            "Loan fine must be paid before returning the book"
        )


class NotFoundException(DomainException):
    pass


class UnauthorizedException(DomainException):
    pass
