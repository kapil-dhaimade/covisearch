import enum


# NOTE: KAPIL: Named this 'mytypes' instead of 'types' because the name 'types' conflicts
# with some internal Python module and gives error "module 'enum' has no attribute 'Enum'"
# while debugging modules of covisearch.util.


URL = str


class ContentType(enum.Enum):
    HTML = 1
    JSON = 2
