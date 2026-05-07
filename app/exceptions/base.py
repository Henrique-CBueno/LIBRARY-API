class DomainException(Exception):
    pass


class BusinessRuleException(DomainException):
    pass


class NotFoundException(DomainException):
    pass


class UnauthorizedException(DomainException):
    pass