import pytest
from mock import MagicMock, patch

from prequ._pip_compat import (
    PIP_10_OR_NEWER, PackageFinder, install_req_from_line)
from prequ.repositories.pypi import PyPIRepository
from prequ.scripts._repo import get_pip_command


def test_pypirepo_build_dir_is_str():
    assert isinstance(get_pypi_repository().build_dir, str)


def test_pypirepo_source_dir_is_str():
    assert isinstance(get_pypi_repository().source_dir, str)


@pytest.mark.skipif(PIP_10_OR_NEWER, reason="Needs Pip 9 or older")
def test_pypirepo_calls_reqset_with_str_paths():
    """
    Make sure that paths passed to RequirementSet init are str.

    Passing unicode paths on Python 2 could make pip fail later on
    unpack, if the package contains non-ASCII file names, because
    non-ASCII str and unicode paths cannot be combined.
    """
    with patch('prequ.repositories.pypi.RequirementSet') as mocked_init:
        repo = get_pypi_repository()
        ireq = install_req_from_line('ansible==2.4.0.0')

        # Setup a mock object to be returned from the RequirementSet call
        mocked_reqset = MagicMock()
        mocked_init.return_value = mocked_reqset

        # Fill link for ireq, because get_dependencies uses it as a cache key
        ireq.link = MagicMock(url='http://localhost/ansible2400.zip')

        # Do the call
        repo.get_dependencies(ireq)

        # Check that RequirementSet init is called with correct type arguments
        assert mocked_init.call_count == 1
        (init_call_args, init_call_kwargs) = mocked_init.call_args
        assert isinstance(init_call_args[0], str)
        assert isinstance(init_call_args[1], str)
        assert isinstance(init_call_kwargs.get('download_dir'), str)
        assert isinstance(init_call_kwargs.get('wheel_download_dir'), str)

        # Check that _prepare_file is called correctly
        assert mocked_reqset._prepare_file.call_count == 1
        (pf_call_args, pf_call_kwargs) = mocked_reqset._prepare_file.call_args
        (called_with_finder, called_with_ireq) = pf_call_args
        assert isinstance(called_with_finder, PackageFinder)
        assert called_with_ireq == ireq
        assert not pf_call_kwargs


@pytest.mark.skipif(not PIP_10_OR_NEWER, reason="Needs Pip 10 or newer")
@patch('prequ.repositories.pypi.RequirementSet')
@patch('prequ.repositories.pypi.PipResolver')
@patch('prequ.repositories.pypi.RequirementPreparer')
def test_pypirepo_calls_preparer_with_str_paths(
        mocked_init, mocked_resolver, mocked_reqset):
    """
    Make sure that paths passed to RequirementPreparer init are str.

    Similar to `test_pypirepo_calls_reqset_with_str_paths` but for Pip 10.
    """
    repo = get_pypi_repository()
    ireq = install_req_from_line('ansible==2.4.0.0')
    ireq.link = MagicMock(url='http://localhost/ansible2400.zip')

    mocked_resolve_func = MagicMock()
    mocked_resolver.resolve.return_value = mocked_resolve_func

    repo.get_dependencies(ireq)

    # Check that RequirementPreparer init is called with correct
    # type arguments
    assert mocked_init.call_count == 1
    (init_call_args, init_call_kwargs) = mocked_init.call_args
    assert isinstance(init_call_kwargs.get('build_dir'), str)
    assert isinstance(init_call_kwargs.get('src_dir'), str)
    assert isinstance(init_call_kwargs.get('download_dir'), str)
    assert isinstance(init_call_kwargs.get('wheel_download_dir'), str)


def get_pypi_repository():
    """
    Get a PyPIRepository object for the tests.

    :rtype: PyPIRepository
    """
    pip_command = get_pip_command()
    pip_options = pip_command.parse_args([])[0]
    session = pip_command._build_session(pip_options)
    return PyPIRepository(pip_options, session)
