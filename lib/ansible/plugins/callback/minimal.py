# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase
from ansible import constants as C


class CallbackModule(CallbackBase):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'minimal'

    def _command_generic_msg(self, host, result,  caption):
        ''' output the result of a command run '''

        buf = "%s | %s | rc=%s >>\n" % (host, caption, result.get('rc',0))
        buf += result.get('stdout','')
        buf += result.get('stderr','')
        buf += result.get('msg','')

        return buf + "\n"

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if 'exception' in result._result:
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result._result['exception'].strip().split('\n')[-1]
                msg = "An exception occurred during task execution. To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = "An exception occurred during task execution. The full traceback is:\n" + result._result['exception']

            self._display.display(msg, color='red')

            # finally, remove the exception from the result so it's not shown every time
            del result._result['exception']

        if result._task.action in C.MODULE_NO_JSON:
            self._display.display(self._command_generic_msg(result._host.get_name(), result._result,"FAILED"), color='red')
        else:
            abridged_result = result.copy(result._result)
            abridged_result.pop('invocation', None)
            self._display.display("%s | FAILED! => %s" % (result._host.get_name(), self._dump_results(abridged_result, indent=4)), color='red')

    def v2_runner_on_ok(self, result):
        if result._task.action in C.MODULE_NO_JSON:
            self._display.display(self._command_generic_msg(result._host.get_name(), result._result,"SUCCESS"), color='green')
        else:
            abridged_result = result.copy(result._result)
            abridged_result.pop('invocation', None)
            self._display.display("%s | SUCCESS => %s" % (result._host.get_name(), self._dump_results(abridged_result, indent=4)), color='green')
            self._handle_warnings(result._result)

    def v2_runner_on_skipped(self, result):
        self._display.display("%s | SKIPPED" % (result._host.get_name()), color='cyan')

    def v2_runner_on_unreachable(self, result):
        abridged_result = result.copy(result._result)
        abridged_result.pop('invocation', None)
        self._display.display("%s | UNREACHABLE! => %s" % (result._host.get_name(), self._dump_results(abridged_result, indent=4)), color='yellow')

    def v2_on_file_diff(self, result):
        if 'diff' in result._result and result._result['diff']:
            self._display.display(self._get_diff(result._result['diff']))
