# Copyright (c) 2015. Librato, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Librato, Inc. nor the names of project contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL LIBRATO, INC. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from math import floor
import time

from librato_python_web.instrumentor.instrument import function_wrapper_factory
from librato_python_web.instrumentor.instrumentor import BaseInstrumentor
from librato_python_web.instrumentor import context as context
from librato_python_web.instrumentor import telemetry
from librato_python_web.instrumentor.util import get_parameter, Timing


def requests_request_time(f):
    def inner_requests_request_time(*args, **keywords):
        method = get_parameter(0, 'method', *args, **keywords)
        url = get_parameter(1, 'url', *args, **keywords)
        with context.add_all_tags([('external.url', url), ('external.method', method)]):
            telemetry.count('external.http.requests')
            t = Timing.start_timer('external.requests')
            try:
                a = f(*args, **keywords)
                telemetry.count('external.http.status.%ixx' % floor(a.status_code / 100))
                return a
            except:
                telemetry.count('external.http.errors')
                raise
            finally:
                elapsed = Timing.stop_timer('external.requests')
                telemetry.record('external.http.response.latency', elapsed)

    return inner_requests_request_time


class RequestsInstrumentor(BaseInstrumentor):
    required_class_names = ['requests.api']

    def __init__(self):
        super(RequestsInstrumentor, self).__init__(
            {
                # External calls are not recorded when in the context of a model operation
                'requests.api.request': function_wrapper_factory(requests_request_time, state='external',
                                                                 disable_if='model')
            }
        )

    def run(self):
        super(RequestsInstrumentor, self).run()
