from collections.abc import Iterable, Iterator
from itertools import islice


def batched(
    iterable: Iterable,
    batch_size: int,
) -> Iterator[list]:
    iterator = iter(iterable)

    while batch := list(islice(iterator, batch_size)):
        yield batch