class GenerationCancelled(Exception):
    """The user cancelled generation before the output was published."""


def check_cancel(cancel):
    if cancel is not None and cancel():
        raise GenerationCancelled('Book generation cancelled')
