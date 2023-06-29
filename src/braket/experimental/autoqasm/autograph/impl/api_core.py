# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""This module contains the user- and codegen-facing API for AutoGraph."""

import inspect
import os
import sys
import traceback

from braket.experimental.autoqasm.autograph.pyct import error_utils
from braket.experimental.autoqasm.autograph.pyct import errors
from braket.experimental.autoqasm.autograph.pyct import origin_info
from braket.experimental.autoqasm.autograph.logging import ag_logging as logging
from braket.experimental.autoqasm.autograph.tf_utils import tf_stack
import inspect as tf_inspect


def is_autograph_strict_conversion_mode():
  return int(os.environ.get('AUTOGRAPH_STRICT_CONVERSION', '0')) > 0


def _log_callargs(f, args, kwargs):
  """Logging helper."""
  logging.log(2, 'Defaults of %s : %s', f, f.__defaults__)
  logging.log(2, 'KW defaults of %s : %s', f, f.__kwdefaults__)

  if kwargs is not None:
    callargs = tf_inspect.getcallargs(f, *args, **kwargs)
  else:
    callargs = tf_inspect.getcallargs(f, *args)

  formatted_callargs = '\n'.join(
      '    {}: {}'.format(k, v) for k, v in callargs.items())
  logging.log(2, 'Calling %s with\n%s\n', f, formatted_callargs)


#
# Error handling
#


# TODO(mdan): Export this symbol.
class AutoGraphError(errors.PyCTError):
  """Base class for all AutoGraph exceptions."""
  pass


class ConversionError(AutoGraphError):
  """Raised during the conversion process."""
  pass


class StagingError(AutoGraphError):
  """Raised during the staging (i.e. Python execution) of converted code."""
  pass


class _ErrorMetadata(error_utils.ErrorMetadataBase):
  """AutoGraph-specific error metadata. See base class."""

  def create_exception(self, source_error):
    preferred_type = type(source_error)
    if preferred_type in (errors.PyCTError, AutoGraphError, ConversionError,
                            StagingError):
      return preferred_type(self.get_message())

    exc = super(_ErrorMetadata, self).create_exception(source_error)
    if exc is not None:
      return exc

    # Note: While changing an error's message property to change the message it
    # displays will probably work a lot of times, there is no standard way in
    # Python to do that. The safest way is therefore to create a new exception.
    # For user defined exceptions, we could define an interface that allowed
    # them to work under this mechanism.
    return StagingError(self.get_message())


def _attach_error_metadata(e, f):
  """Augments an error with the metadata necessary for rewrite."""
  if hasattr(e, 'ag_pass_through'):
    return

  metadata = getattr(e, 'ag_error_metadata', None)
  source_map = f.ag_source_map

  if metadata is None:
    logging.log(1, 'Caught error in user callable %s', f, exc_info=True)
    message = '{}: {}'.format(e.__class__.__name__, e)
  else:
    message = None

  cause_tb = traceback.extract_tb(sys.exc_info()[2])[1:]

  e.ag_error_metadata = _ErrorMetadata(cause_tb, metadata, message, source_map,
                                       __file__)


class StackTraceMapper(tf_stack.StackTraceMapper):
  """Remaps generated code to code it originated from."""

  def __init__(self, converted_fn):
    super().__init__()
    self._source_map = converted_fn.ag_source_map
    # This may be called repeatedly: once on entry, by the superclass, then by
    # each child context manager.
    self._cached_map = None

  def get_effective_source_map(self):
    if self._cached_map is not None:
      return self._cached_map

    parent_map = self.parent.get_effective_source_map()

    effective_source_map = {}
    for loc, origin in self._source_map.items():
      effective_source_map[(loc.filename, loc.lineno)] = (origin.loc.filename,
                                                          origin.loc.lineno,
                                                          origin.function_name)

    for key, value in parent_map.items():
      filename, lineno, _ = value
      value_loc = origin_info.LineLocation(filename=filename, lineno=lineno)
      if value_loc in self._source_map:
        origin = self._source_map[value_loc]
        effective_source_map[key] = (origin.loc.filename, origin.loc.lineno,
                                     origin.function_name)
      else:
        effective_source_map[key] = value

    self._cached_map = effective_source_map
    return effective_source_map


#
# Generated code support
#


def autograph_artifact(entity, extras=None):
  if inspect.ismethod(entity):
    setattr(entity.__func__, 'autograph_info__', extras)
  else:
    setattr(entity, 'autograph_info__', extras)
  return entity


def is_autograph_artifact(entity):
  return hasattr(entity, 'autograph_info__')
