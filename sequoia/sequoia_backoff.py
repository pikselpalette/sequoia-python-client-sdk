import copy
import logging

import backoff

from sequoia import error


class SequoiaBackoff:
    def __init__(self, backoff_strategy):
        self.backoff_strategy = backoff_strategy

    def run_with_backoff(self, func, *func_args, **func_kwargs):
        def fatal_code(e):
            return isinstance(e, error.HttpError) and \
                   400 <= e.status_code < 500 and e.status_code != 429

        def backoff_hdlr(details):
            logging.warning('Retry `%s` for args `%s` and kwargs `%s`', details['tries'], details['args'],
                            details['kwargs'])

        decorated_request = backoff.on_exception(self.backoff_strategy.pop('wait_gen', backoff.constant),
                                                 (error.ConnectionError, error.Timeout, error.TooManyRedirects,
                                                  error.HttpError),
                                                 giveup=fatal_code,
                                                 on_backoff=backoff_hdlr,
                                                 **copy.deepcopy(self.backoff_strategy))(func)
        return decorated_request(*func_args, **func_kwargs)
