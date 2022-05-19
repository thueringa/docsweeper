"""Command line interface."""
from __future__ import annotations

import configparser
import logging
import multiprocessing.dummy
import sys
import warnings
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Type,
)

if sys.version_info < (3, 8):
    from importlib_metadata import metadata, version
else:
    from importlib.metadata import version, metadata

import click

from _docsweeper import configure_logger
from _docsweeper.docsweeper import (
    DocumentedToken,
    DocumentedTokenStatistic,
    ParserError,
    analyze_file,
)
from _docsweeper.result_handler import ClickResultHandler
from _docsweeper.version_control import (
    VCSCommandSet,
    VCSCommandSetConfig,
    VCSExecutableError,
    command_sets,
)

logger = logging.getLogger(__name__)


class _AnonymousGroup(click.Group):
    """Anonymous click command group.

    This implementation removes the entry in the usage string for the group's own
    COMMAND and further ARGs, which :class:`click.Group` adds by default.

    """

    def collect_usage_pieces(self, ctx: click.Context) -> List[str]:
        # call method 'collect_usage_pieces' of grandparent class 'click.Command', and
        # not 'click.Group':
        return click.Command.collect_usage_pieces(self, ctx)


class _DocsweeperGroup(_AnonymousGroup):
    """Prints a specially formatted help epilogue that lists available shims."""

    def format_epilog(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Write the epilog into the formatter if it exists."""
        with formatter.section(
            "Supported version control systems and their default executables"
        ):
            formatter.write_dl(
                [
                    (command_set.name, str(config.executable))
                    for command_set, config in command_sets.values()
                ]
            )


class _UnknownConfigException(Exception):
    """Raised upon encountering an unsupported configuration value or section."""

    def __init__(self, file_: str, section: str, option: Optional[str] = None) -> None:
        """Raise exception for unknown option *option* in section *section* of *file_*.

        :param file_: path of the configuration file where the unknown element was found
        :param section: section where the unknown element was found
        :param option: the option that was unknown. If *option* is ``None``, it is
            assumed that *section* is the unknown element instead.

        """
        message = f"Error parsing configuration file {file_}: "
        if option is None:
            message += f"section '{section}' not supported."
        else:
            message += f"option '{option}' in section '{section}' not supported."
        self.message = message
        super().__init__(self.message)


class _ParsedArgs(NamedTuple):
    """Holds parsed command line arguments in a form usable by internal classes."""

    vcs_command_set_type: Type[VCSCommandSet]
    """the type of version control command set used"""
    vcs_command_set_config: VCSCommandSetConfig
    """configuration for the version control command set"""
    files: Sequence[Path]
    """list of files that are to be analyzed"""
    debug: Optional[bool]
    """whether debug mode is activated"""
    verbose: Optional[bool]
    """whether verbose mode is activated"""


def _handle_vcs_command_set_type_arg(
    ctx: click.Context, param: click.Option, value: Optional[str]
) -> Optional[Type[VCSCommandSet]]:
    if value is None:
        return None
    return command_sets[value][0]


def _handle_verbosity_arg(
    ctx: click.Context, param: click.Option, value: Optional[bool]
) -> Optional[bool]:
    if value:
        configure_logger(logging.INFO)
    return value


def _handle_debug_arg(
    ctx: click.Context, param: click.Option, value: Optional[bool]
) -> Optional[bool]:
    if value:
        configure_logger(logging.DEBUG)
    return value


def _handle_config_arg(
    ctx: click.Context, param: click.Option, value: Optional[Path]
) -> configparser.ConfigParser:
    config_path = value

    # Read default config:
    config = _create_default_ini_config(command_sets)

    # Update config with user-provided values, if supported:
    if config_path:
        logger.info(f"Reading user provided config file '{config_path}'")
        try:
            with open(config_path) as file_:
                user_config = configparser.ConfigParser()
                user_config.read_file(file_)
                for section in user_config.sections():
                    if not config.has_section(section):
                        raise _UnknownConfigException(str(config_path), section)
                    for option in user_config.options(section):
                        if not config.has_option(section, option):
                            raise _UnknownConfigException(
                                str(config_path), section, option
                            )
                        config.set(section, option, user_config.get(section, option))
        except (OSError, _UnknownConfigException) as exp:
            print(
                f"Could not read config file '{value}'! Reason: {exp}",
                file=sys.stderr,
            )
            sys.exit(2)
    return config


def _handle_version_arg(
    ctx: click.Context, param: click.Option, value: Optional[bool]
) -> None:
    if value:
        name = metadata("docsweeper")["Name"].capitalize()
        version_ = version("docsweeper")
        click.echo(f"{name} v{version_}")
        sys.exit(0)


def _create_default_ini_config(
    command_sets: Dict[str, Tuple[Type[VCSCommandSet], VCSCommandSetConfig]]
) -> configparser.ConfigParser:
    """Return a default ini-style configuration for all the available command sets.

    :param command_sets: the available command sets
    :returns: a populated configuration with values from *command_sets*

    """
    config = configparser.ConfigParser()
    config_dict = {
        "docsweeper": {
            "vcs": command_sets["git"][0].name,
            "follow_rename": command_sets["git"][1].follow_rename,
        }
    }
    config_dict.update(
        {
            f"docsweeper.{command_set.name}": {"executable": str(config.executable)}
            for command_set, config in command_sets.values()
        }
    )
    config.read_dict(config_dict)
    return config


def _handle_deprecated_vcs_shim_arg(
    ctx: click.Context, param: click.Option, value: Optional[str]
) -> Any:
    if value:
        warning = (
            "Command line option --vcs-shim is DEPRECATED since Docsweeper v1.2.0! Use "
            "--vcs instead."
        )
        warnings.warn(warning, FutureWarning)
        return _handle_vcs_command_set_type_arg(ctx, _vcs_option, value)
    return None


class _VCSOption(click.Option):

    _help_string = (
        "History of FILEs will be retrieved using this version control system. "
    )

    def __init__(
        self,
        param_decls: Optional[Sequence[str]],
        callback: Optional[Callable[[click.core.Context, click.Parameter, Any], Any]],
        help_prefix: Optional[str] = None,
    ) -> None:
        super().__init__(
            param_decls=param_decls,
            default=None,
            help="".join(
                [
                    help_prefix if help_prefix else "",
                    _VCSOption._help_string,
                ]
            ),
            type=click.Choice(list(command_sets.keys())),
            callback=_handle_vcs_command_set_type_arg,
            show_default=list(command_sets.keys())[0],
        )


_vcs_option = _VCSOption(
    ["vcs_command_set_type", "--vcs"], _handle_vcs_command_set_type_arg  # type: ignore
)
_vcs_executable_option = click.Option(
    [
        "vcs_executable",
        "-e",
        "--vcs-executable",
    ],
    help=(
        "the version control executable located at PATH will be used during "
        "analysis. See below for the default value of each supported version "
        "control system."
    ),
    default=None,
    type=click.Path(path_type=Path),
)
_no_follow_rename_option = click.Option(
    [
        "no_follow_rename",
        "--no-follow-rename",
    ],
    default=None,
    help="Do not follow renames of files.",
    is_flag=True,
)
_config_option = click.Option(
    [
        "-c",
        "--config",
    ],
    help="Load a Docsweeper configuration file located at PATH.",
    default=None,
    type=click.Path(path_type=Path),
    callback=_handle_config_arg,
)
_verbose_option = click.Option(
    [
        "-v",
        "--verbose",
    ],
    help="Set verbose mode.",
    callback=_handle_verbosity_arg,
    is_flag=True,
)
_debug_option = click.Option(
    [
        "-d",
        "--debug",
    ],
    help="Set debugging mode. Lots of messages.",
    callback=_handle_debug_arg,
    is_flag=True,
)
_version_option = click.Option(
    [
        "-V",
        "--version",
    ],
    help="Show version information.",
    default=None,
    is_flag=True,
    callback=_handle_version_arg,
    expose_value=False,
)
_vcs_shim_option = _VCSOption(
    ["vcs_command_set_type", "--vcs-shim"],
    _handle_deprecated_vcs_shim_arg,  # type: ignore
    'DEPRECATED since v1.2.0! Use option "--vcs" instead. ',
)


def _parse_args_decorator(f):  # type: ignore
    """Wrap around the decorators of :func:`parse_args`.

    This is needed so that sphinx can generate documentation correctly.

    :param f: the function that is wrapped
    :returns: the wrapped function with correct docs
    """

    @wraps(f)
    @click.group(
        invoke_without_command=True,
        cls=_DocsweeperGroup,
        context_settings={"help_option_names": ["--help", "-h"]},
        params=[
            _vcs_option,
            _vcs_executable_option,
            _no_follow_rename_option,
            _config_option,
            _verbose_option,
            _debug_option,
            _version_option,
            _vcs_shim_option,
        ],
    )
    @click.argument(
        "files",
        type=click.Path(path_type=Path),
        nargs=-1,
        metavar="FILE...",
        required=True,
    )
    def wrapper(*args, **kwds):  # type:ignore
        # This is used used by click as the short command help.
        """Analyze FILE or multiple FILEs for outdated docstrings."""
        return f(*args, **kwds)

    return wrapper


@_parse_args_decorator  # type:ignore
def parse_args(
    files: Tuple[Path],
    vcs_command_set_type: Type[VCSCommandSet],
    vcs_executable: Optional[Path],
    config: configparser.ConfigParser,
    no_follow_rename: Optional[bool],
    verbose: Optional[bool],
    debug: Optional[bool],
) -> _ParsedArgs:
    """Validate command line arguments and transform them into a configuration object.

    :param files: list of files that are to be analyzed
    :param vcs_command_set_type: type of the version control command set that is to be
        used
    :param vcs_executable: location of the executable of the version control system
    :param config: .ini configuration file
    :param no_follow_rename: if ``True``, do not follow renames
    :param debug: state of debug mode
    :param verbose: state of verbose mode
    :returns: the configuration object

    """

    follow_rename = _get_rename_follow_status(config, no_follow_rename)
    vcs_command_set_type = _get_vcs_type_status(config, vcs_command_set_type)
    executable = (
        vcs_executable
        if vcs_executable
        else Path(config.get(f"docsweeper.{vcs_command_set_type.name}", "executable"))
    )
    vcs_command_set_config = VCSCommandSetConfig(
        executable=executable, follow_rename=follow_rename
    )
    parsed_args = _ParsedArgs(
        vcs_command_set_config=vcs_command_set_config,
        vcs_command_set_type=vcs_command_set_type,
        files=list(files),
        verbose=verbose,
        debug=debug,
    )
    return parsed_args


def _run_decorator(f):  # type:ignore
    """Wrap around the decorators of :func:`run`.

    This is needed so that sphinx can generate documentation correctly.

    :param f: the function that is wrapped
    :returns: the wrapped function with correct docs

    """

    @wraps(f)
    @parse_args.result_callback()
    def wrapper(*args, **kwds):  # type:ignore
        return f(*args, **kwds)

    return wrapper


@_run_decorator  # type:ignore
def run(parsed_args: _ParsedArgs, **kwargs) -> None:  # type:ignore
    """Run the analysis using the configuration in *parsed_args*.

    Registered as a callback to :func:`parse_args`.

    :param parsed_args: command configuration as returned by :func:`parse_args`
    :raises SystemExit: if there occurs an unrecoverable error during analysis
    :raises Exception: re-raise unexpected expections if debug mode is activated in
        *parsed_args*. Only print error message otherwise.

    # noqa: DAR101,DAR401

    """
    result_handler = ClickResultHandler()

    def do(
        file_: Path,
    ) -> Tuple[
        Path,
        Optional[List[Tuple[DocumentedToken, DocumentedTokenStatistic]]],
        Optional[Exception],
    ]:
        """Return statistics for all tokens in *file_*.

        :param file_: path of the file
        :returns: a tuple consisting of
            - the path to *file*, and
            - a list of tuples, each consisting of a documented token in *file* and its
              corresponding docstring statistic

        """
        try:
            return (
                file_,
                analyze_file(
                    parsed_args.vcs_command_set_type,
                    parsed_args.vcs_command_set_config,
                    file_.resolve(),
                ),
                None,
            )
        except Exception as exception:
            return file_, None, exception

    with multiprocessing.dummy.Pool() as pool:
        analysis_results = pool.map(do, parsed_args.files)
    for file_, result, error in analysis_results:
        if error:
            if isinstance(error, (VCSExecutableError, ParserError)):
                # expected errors
                raise SystemExit(f"Error analyzing '{file_}': {error}") from error
            else:
                # unexpected errors
                message = f"Unexpected error occured: {error}. "
                print(message, file=sys.stderr)
                if parsed_args.debug:
                    raise error
                else:
                    raise SystemExit(
                        "Run command with option '-d/--debug' for full stack trace."
                    )
        for token, token_history in result:
            result_handler.handle_result(file_, token, token_history)


def _get_vcs_type_status(
    config: configparser.ConfigParser, parsed_args: Optional[Type[VCSCommandSet]]
) -> Type[VCSCommandSet]:
    if parsed_args:
        return parsed_args
    if config.has_option("docsweeper", "vcs"):
        config_vcs = config.get("docsweeper", "vcs")
        if config_vcs in command_sets.keys():
            return command_sets[config_vcs][0]
        else:
            raise SystemExit(f"Unknown version control system {config_vcs}")
    return command_sets[list(command_sets)[0]][0]


def _get_rename_follow_status(
    config: configparser.ConfigParser, parsed_args: Optional[bool]
) -> bool:
    if parsed_args:
        return False
    if config.has_option("docsweeper", "follow_rename"):
        return config.getboolean("docsweeper", "follow_rename")
    return True
