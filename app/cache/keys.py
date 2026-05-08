def book_detail_key(book_id):
    return f"book:{book_id}"


def books_list_key(
    page,
    size,
    title,
    category,
    author,
    available,
):
    return (
        f"books:list:"
        f"{page}:{size}:"
        f"{title}:{category}:"
        f"{author}:{available}"
    )