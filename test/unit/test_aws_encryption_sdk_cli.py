# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
"""Unit test suite for ``aws_encryption_sdk_cli``."""
import logging

import aws_encryption_sdk
from mock import MagicMock, sentinel
import pytest

import aws_encryption_sdk_cli
from aws_encryption_sdk_cli.exceptions import BadUserArgumentError


def patch_reactive_side_effect(kwargs):
    def _check(path):
        return kwargs[path]
    return _check


@pytest.fixture
def patch_for_process_cli_request(mocker):
    mocker.patch.object(aws_encryption_sdk_cli.os.path, 'isdir')
    mocker.patch.object(aws_encryption_sdk_cli.os.path, 'isfile')
    mocker.patch.object(aws_encryption_sdk_cli, 'process_dir')
    mocker.patch.object(aws_encryption_sdk_cli, 'output_filename')
    aws_encryption_sdk_cli.output_filename.return_value = sentinel.destination_filename
    mocker.patch.object(aws_encryption_sdk_cli, 'process_single_file')
    mocker.patch.object(aws_encryption_sdk_cli, 'process_single_operation')


def test_process_cli_request_source_is_destination(patch_for_process_cli_request):
    with pytest.raises(BadUserArgumentError) as excinfo:
        aws_encryption_sdk_cli.process_cli_request(
            stream_args=sentinel.stream_args,
            source=sentinel.source,
            destination=sentinel.source,
            recursive=True,
            interactive=sentinel.interactive,
            no_overwrite=sentinel.no_overwrite
        )
    excinfo.match(r'Destination and source cannot be the same')


def test_process_cli_request_source_dir_nonrecursive(patch_for_process_cli_request):
    aws_encryption_sdk_cli.os.path.isdir.side_effect = patch_reactive_side_effect({
        sentinel.source: True,
        sentinel.destination: True
    })
    with pytest.raises(BadUserArgumentError) as excinfo:
        aws_encryption_sdk_cli.process_cli_request(
            stream_args=sentinel.stream_args,
            source=sentinel.source,
            destination=sentinel.destination,
            recursive=False,
            interactive=sentinel.interactive,
            no_overwrite=sentinel.no_overwrite
        )
    excinfo.match(r'Must specify -r/-R/--recursive when operating on a source directory')


def test_process_cli_request_source_dir_destination_nondir(patch_for_process_cli_request):
    aws_encryption_sdk_cli.os.path.isdir.side_effect = patch_reactive_side_effect({
        sentinel.source: True,
        sentinel.destination: False
    })
    with pytest.raises(BadUserArgumentError) as excinfo:
        aws_encryption_sdk_cli.process_cli_request(
            stream_args=sentinel.stream_args,
            source=sentinel.source,
            destination=sentinel.destination,
            recursive=True,
            interactive=sentinel.interactive,
            no_overwrite=sentinel.no_overwrite
        )
    excinfo.match(r'If operating on a source directory, destination must be an existing directory')


def test_process_cli_request_source_dir_destination_dir(patch_for_process_cli_request):
    aws_encryption_sdk_cli.os.path.isdir.side_effect = patch_reactive_side_effect({
        sentinel.source: True,
        sentinel.destination: True
    })
    aws_encryption_sdk_cli.os.path.isfile.side_effect = patch_reactive_side_effect({
        sentinel.source: False
    })
    aws_encryption_sdk_cli.process_cli_request(
        stream_args=sentinel.stream_args,
        source=sentinel.source,
        destination=sentinel.destination,
        recursive=True,
        interactive=sentinel.interactive,
        no_overwrite=sentinel.no_overwrite
    )
    aws_encryption_sdk_cli.process_dir.assert_called_once_with(
        stream_args=sentinel.stream_args,
        source=sentinel.source,
        destination=sentinel.destination,
        interactive=sentinel.interactive,
        no_overwrite=sentinel.no_overwrite
    )
    assert not aws_encryption_sdk_cli.os.path.isfile.called
    assert not aws_encryption_sdk_cli.output_filename.called
    assert not aws_encryption_sdk_cli.process_single_file.called
    assert not aws_encryption_sdk_cli.process_single_operation.called


def test_process_cli_request_source_stdin_destination_dir(patch_for_process_cli_request):
    aws_encryption_sdk_cli.os.path.isdir.side_effect = patch_reactive_side_effect({
        '-': False,
        sentinel.destination: True
    })
    with pytest.raises(BadUserArgumentError) as excinfo:
        aws_encryption_sdk_cli.process_cli_request(
            stream_args=sentinel.stream_args,
            source='-',
            destination=sentinel.destination,
            recursive=False,
            interactive=sentinel.interactive,
            no_overwrite=sentinel.no_overwrite
        )
    excinfo.match(r'Destination may not be a directory when source is stdin')


def test_process_cli_request_source_stdin(patch_for_process_cli_request):
    aws_encryption_sdk_cli.os.path.isdir.side_effect = patch_reactive_side_effect({
        '-': False,
        sentinel.destination: False
    })
    aws_encryption_sdk_cli.process_cli_request(
        stream_args=sentinel.stream_args,
        source='-',
        destination=sentinel.destination,
        recursive=False,
        interactive=sentinel.interactive,
        no_overwrite=sentinel.no_overwrite
    )
    assert not aws_encryption_sdk_cli.process_dir.called
    assert not aws_encryption_sdk_cli.os.path.isfile.called
    assert not aws_encryption_sdk_cli.output_filename.called
    assert not aws_encryption_sdk_cli.process_single_file.called
    aws_encryption_sdk_cli.process_single_operation.assert_called_once_with(
        stream_args=sentinel.stream_args,
        source='-',
        destination=sentinel.destination,
        interactive=sentinel.interactive,
        no_overwrite=sentinel.no_overwrite
    )


def test_process_cli_request_source_file_destination_dir(patch_for_process_cli_request):
    aws_encryption_sdk_cli.os.path.isdir.side_effect = patch_reactive_side_effect({
        sentinel.source: False,
        sentinel.destination: True
    })
    aws_encryption_sdk_cli.os.path.isfile.side_effect = patch_reactive_side_effect({
        sentinel.source: True
    })
    aws_encryption_sdk_cli.process_cli_request(
        stream_args={'mode': sentinel.mode},
        source=sentinel.source,
        destination=sentinel.destination,
        recursive=False,
        interactive=sentinel.interactive,
        no_overwrite=sentinel.no_overwrite
    )
    assert not aws_encryption_sdk_cli.process_dir.called
    assert not aws_encryption_sdk_cli.process_single_operation.called
    aws_encryption_sdk_cli.os.path.isfile.assert_called_once_with(sentinel.source)
    aws_encryption_sdk_cli.output_filename.assert_called_once_with(
        source_filename=sentinel.source,
        destination_dir=sentinel.destination,
        mode=sentinel.mode
    )
    aws_encryption_sdk_cli.process_single_file.assert_called_once_with(
        stream_args={'mode': sentinel.mode},
        source=sentinel.source,
        destination=sentinel.destination_filename,
        interactive=sentinel.interactive,
        no_overwrite=sentinel.no_overwrite
    )


def test_process_cli_request_source_file_destination_file(patch_for_process_cli_request):
    aws_encryption_sdk_cli.os.path.isdir.side_effect = patch_reactive_side_effect({
        sentinel.source: False,
        sentinel.destination: False
    })
    aws_encryption_sdk_cli.os.path.isfile.side_effect = patch_reactive_side_effect({
        sentinel.source: True
    })
    aws_encryption_sdk_cli.process_cli_request(
        stream_args={'mode': sentinel.mode},
        source=sentinel.source,
        destination=sentinel.destination,
        recursive=False,
        interactive=sentinel.interactive,
        no_overwrite=sentinel.no_overwrite
    )
    assert not aws_encryption_sdk_cli.process_dir.called
    assert not aws_encryption_sdk_cli.process_single_operation.called
    aws_encryption_sdk_cli.os.path.isfile.assert_called_once_with(sentinel.source)
    assert not aws_encryption_sdk_cli.output_filename.called
    aws_encryption_sdk_cli.process_single_file.assert_called_once_with(
        stream_args={'mode': sentinel.mode},
        source=sentinel.source,
        destination=sentinel.destination,
        interactive=sentinel.interactive,
        no_overwrite=sentinel.no_overwrite
    )


def test_process_cli_request_invalid_source(patch_for_process_cli_request):
    aws_encryption_sdk_cli.os.path.isdir.side_effect = patch_reactive_side_effect({
        sentinel.source: False,
        sentinel.destination: False
    })
    aws_encryption_sdk_cli.os.path.isfile.side_effect = patch_reactive_side_effect({
        sentinel.source: False
    })
    with pytest.raises(BadUserArgumentError) as excinfo:
        aws_encryption_sdk_cli.process_cli_request(
            stream_args=sentinel.stream_args,
            source=sentinel.source,
            destination=sentinel.destination,
            recursive=False,
            interactive=sentinel.interactive,
            no_overwrite=sentinel.no_overwrite
        )
    excinfo.match(r'Invalid source.  Must be a filename, directory, or stdin \(-\)')


@pytest.mark.parametrize('args, stream_args', (
    (
        MagicMock(
            action=sentinel.mode,
            encryption_context=None,
            algorithm=None,
            frame_length=None,
            max_length=None
        ),
        {
            'materials_manager': sentinel.materials_manager,
            'mode': sentinel.mode
        }
    ),
    (
        MagicMock(
            action=sentinel.mode,
            encryption_context=None,
            algorithm=None,
            frame_length=None,
            max_length=sentinel.max_length
        ),
        {
            'materials_manager': sentinel.materials_manager,
            'mode': sentinel.mode,
            'max_body_length': sentinel.max_length
        }
    ),
    (
        MagicMock(
            action=sentinel.mode,
            encryption_context=None,
            algorithm=None,
            frame_length=None,
            max_length=None
        ),
        {
            'materials_manager': sentinel.materials_manager,
            'mode': sentinel.mode,
        }
    ),
    (
        MagicMock(
            action=sentinel.mode,
            encryption_context=sentinel.encryption_context,
            algorithm='AES_256_GCM_IV12_TAG16_HKDF_SHA384_ECDSA_P384',
            frame_length=sentinel.frame_length,
            max_length=None
        ),
        {
            'materials_manager': sentinel.materials_manager,
            'mode': sentinel.mode,
        }
    ),
    (
        MagicMock(
            action='encrypt',
            encryption_context=sentinel.encryption_context,
            algorithm='AES_256_GCM_IV12_TAG16_HKDF_SHA384_ECDSA_P384',
            frame_length=sentinel.frame_length,
            max_length=None
        ),
        {
            'materials_manager': sentinel.materials_manager,
            'mode': 'encrypt',
            'encryption_context': sentinel.encryption_context,
            'algorithm': aws_encryption_sdk.Algorithm.AES_256_GCM_IV12_TAG16_HKDF_SHA384_ECDSA_P384,
            'frame_length': sentinel.frame_length,
        }
    ),
    (
        MagicMock(
            action='encrypt',
            encryption_context=None,
            algorithm='AES_256_GCM_IV12_TAG16_HKDF_SHA384_ECDSA_P384',
            frame_length=sentinel.frame_length,
            max_length=None
        ),
        {
            'materials_manager': sentinel.materials_manager,
            'mode': 'encrypt',
            'algorithm': aws_encryption_sdk.Algorithm.AES_256_GCM_IV12_TAG16_HKDF_SHA384_ECDSA_P384,
            'frame_length': sentinel.frame_length,
        }
    ),
    (
        MagicMock(
            action='encrypt',
            encryption_context=sentinel.encryption_context,
            algorithm=None,
            frame_length=sentinel.frame_length,
            max_length=None
        ),
        {
            'materials_manager': sentinel.materials_manager,
            'mode': 'encrypt',
            'encryption_context': sentinel.encryption_context,
            'frame_length': sentinel.frame_length
        }
    ),
    (
        MagicMock(
            action='encrypt',
            encryption_context=sentinel.encryption_context,
            algorithm='AES_256_GCM_IV12_TAG16_HKDF_SHA384_ECDSA_P384',
            frame_length=None,
            max_length=None
        ),
        {
            'materials_manager': sentinel.materials_manager,
            'mode': 'encrypt',
            'encryption_context': sentinel.encryption_context,
            'algorithm': aws_encryption_sdk.Algorithm.AES_256_GCM_IV12_TAG16_HKDF_SHA384_ECDSA_P384
        }
    )
))
def test_stream_kwargs_from_args(args, stream_args):
    assert aws_encryption_sdk_cli.stream_kwargs_from_args(args, sentinel.materials_manager) == stream_args


@pytest.fixture
def patch_for_cli(mocker):
    mocker.patch.object(aws_encryption_sdk_cli, 'parse_args')
    aws_encryption_sdk_cli.parse_args.return_value = MagicMock(
        version=False,
        verbosity=None,
        master_keys=sentinel.master_keys,
        caching=sentinel.caching_config,
        input=sentinel.input,
        output=sentinel.output,
        recursive=sentinel.recursive,
        interactive=sentinel.interactive,
        no_overwrite=sentinel.no_overwrite
    )
    mocker.patch.object(aws_encryption_sdk_cli.logging, 'basicConfig')
    mocker.patch.object(aws_encryption_sdk_cli, 'build_crypto_materials_manager_from_args')
    aws_encryption_sdk_cli.build_crypto_materials_manager_from_args.return_value = sentinel.crypto_materials_manager
    mocker.patch.object(aws_encryption_sdk_cli, 'stream_kwargs_from_args')
    aws_encryption_sdk_cli.stream_kwargs_from_args.return_value = sentinel.stream_args
    mocker.patch.object(aws_encryption_sdk_cli, 'process_cli_request')


def test_cli(patch_for_cli):
    test = aws_encryption_sdk_cli.cli(sentinel.raw_args)

    aws_encryption_sdk_cli.parse_args.assert_called_once_with(sentinel.raw_args)
    aws_encryption_sdk_cli.build_crypto_materials_manager_from_args.assert_called_once_with(
        key_providers_config=sentinel.master_keys,
        caching_config=sentinel.caching_config
    )
    aws_encryption_sdk_cli.stream_kwargs_from_args.assert_called_once_with(
        aws_encryption_sdk_cli.parse_args.return_value,
        sentinel.crypto_materials_manager
    )
    aws_encryption_sdk_cli.process_cli_request.assert_called_once_with(
        stream_args=sentinel.stream_args,
        source=sentinel.input,
        destination=sentinel.output,
        recursive=sentinel.recursive,
        interactive=sentinel.interactive,
        no_overwrite=sentinel.no_overwrite
    )
    assert test is aws_encryption_sdk_cli.process_cli_request.return_value


@pytest.mark.parametrize('level, logging_args', (
    (None, {}),
    (-1, {}),
    (0, {}),
    (1, {'level': logging.WARN}),
    (2, {'level': logging.INFO}),
    (3, {'level': logging.DEBUG}),
    (4, {'level': logging.DEBUG})
))
def test_cli_logging_setup(patch_for_cli, level, logging_args):
    aws_encryption_sdk_cli.parse_args.return_value.verbosity = level
    aws_encryption_sdk_cli.cli()
    aws_encryption_sdk_cli.logging.basicConfig.assert_called_once_with(**logging_args)


def test_cli_bad_user_input(patch_for_cli):
    aws_encryption_sdk_cli.process_cli_request.side_effect = BadUserArgumentError(sentinel.error_message)
    test = aws_encryption_sdk_cli.cli()

    assert test is sentinel.error_message
