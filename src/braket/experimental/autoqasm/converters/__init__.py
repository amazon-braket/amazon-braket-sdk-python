# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.


"""AST node-level transformations for code related to AutoQASM types. A converter transformation
injects the content of an AST node into a code template, creating a transformed AST node. The
transformed AST node is the output of a converter. This module implements converters that AutoQASM
overloads or adds on top of AutoGraph.
"""
