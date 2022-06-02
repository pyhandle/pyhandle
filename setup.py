import textwrap
import sys
import os
import os.path
from setuptools import setup, Extension
import platform

# this package is supposed to be installed ONLY on CPython. Try to bail out
# with a meaningful error message in other cases.
if sys.implementation.name != 'cpython':
    msg = 'ERROR: Cannot install and/or update hpy on this python implementation:\n'
    msg += f'    sys.implementation.name == {sys.implementation.name!r}\n\n'
    if '_hpy_universal' in sys.builtin_module_names:
        # this is a python which comes with its own hpy implementation
        import _hpy_universal
        if hasattr(_hpy_universal, 'get_version'):
            hpy_version, git_rev = _hpy_universal.get_version()
            msg += f'This python implementation comes with its own version of hpy=={hpy_version}\n'
            msg += '\n'
            msg += 'If you are trying to install hpy through pip, consider to put the\n'
            msg += 'following in your requirements.txt, to make sure that pip will NOT\n'
            msg += 'try to re-install it:\n'
            msg += f'    hpy=={hpy_version}'
        else:
            msg += 'This python implementation comes with its own version of hpy,\n'
            msg += 'but the exact version could not be determined.\n'
        #
    else:
        # this seems to be a python which does not support hpy
        msg += 'This python implementation does not seem to support hpy:\n'
        msg += '(built-in module _hpy_universal not found).\n'
        msg += 'Please contact your vendor for more informations.'
    sys.exit(msg)


this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

if 'HPY_DEBUG_BUILD' in os.environ:
    # -fkeep-inline-functions is needed to make sure that the stubs for HPy_*
    # functions are available to call inside GDB
    EXTRA_COMPILE_ARGS = [
        '-g', '-O0', '-UNDEBUG',
        '-fkeep-inline-functions',
        #
        ## these flags are useful but don't work on all
        ## platforms/compilers. Uncomment temporarily if you need them.
        #'-Wfatal-errors',    # stop after one error (unrelated to warnings)
        #'-Werror',           # turn warnings into errors
    ]
else:
    EXTRA_COMPILE_ARGS = []

if os.name == "posix" and not '_HPY_DEBUG_FORCE_DEFAULT_MEM_PROTECT' in os.environ:
    EXTRA_COMPILE_ARGS += ['-D_HPY_DEBUG_MEM_PROTECT_USEMMAP']

if platform.system() == "Windows":
    EXTRA_COMPILE_ARGS += ['/WX']
else:
    EXTRA_COMPILE_ARGS += ['-Werror']

def get_scm_config():
    """
    We use this function as a hook to generate version.h before building.
    """
    import textwrap
    import subprocess
    import pathlib
    import setuptools_scm

    version = setuptools_scm.get_version()
    try:
        gitrev = subprocess.check_output('git rev-parse --short HEAD'.split(),
                                         encoding='utf-8')
        gitrev = gitrev.strip()
    except subprocess.CalledProcessError:
        gitrev = "__UNKNOWN__"

    version_h = pathlib.Path('.').joinpath('hpy', 'devel', 'include', 'hpy', 'version.h')
    version_h.write_text(textwrap.dedent(f"""
        // automatically generated by setup.py:get_scm_config()
        #define HPY_VERSION "{version}"
        #define HPY_GIT_REVISION "{gitrev}"
    """))

    version_py = pathlib.Path('.').joinpath('hpy', 'devel', 'version.py')
    version_py.write_text(textwrap.dedent(f"""
        # automatically generated by setup.py:get_scm_config()
        __version__ = "{version}"
        __git_revision__ = "{gitrev}"
    """))

    return {}  # use the default config

EXT_MODULES = [
    Extension('hpy.universal',
              ['hpy/universal/src/hpymodule.c',
               'hpy/universal/src/ctx.c',
               'hpy/universal/src/ctx_meth.c',
               'hpy/universal/src/ctx_misc.c',
               'hpy/devel/src/runtime/argparse.c',
               'hpy/devel/src/runtime/buildvalue.c',
               'hpy/devel/src/runtime/helpers.c',
               'hpy/devel/src/runtime/structseq.c',
               'hpy/devel/src/runtime/ctx_bytes.c',
               'hpy/devel/src/runtime/ctx_call.c',
               'hpy/devel/src/runtime/ctx_capsule.c',
               'hpy/devel/src/runtime/ctx_contextvar.c',
               'hpy/devel/src/runtime/ctx_dict.c',
               'hpy/devel/src/runtime/ctx_err.c',
               'hpy/devel/src/runtime/ctx_module.c',
               'hpy/devel/src/runtime/ctx_object.c',
               'hpy/devel/src/runtime/ctx_type.c',
               'hpy/devel/src/runtime/ctx_tracker.c',
               'hpy/devel/src/runtime/ctx_listbuilder.c',
               'hpy/devel/src/runtime/ctx_tuple.c',
               'hpy/devel/src/runtime/ctx_tuplebuilder.c',
               'hpy/debug/src/debug_ctx.c',
               'hpy/debug/src/debug_ctx_cpython.c',
               'hpy/debug/src/debug_handles.c',
               'hpy/debug/src/dhqueue.c',
               'hpy/debug/src/memprotect.c',
               'hpy/debug/src/stacktrace.c',
               'hpy/debug/src/_debugmod.c',
               'hpy/debug/src/autogen_debug_wrappers.c',
              ],
              include_dirs=[
                  'hpy/devel/include',
                  'hpy/universal/src',
                  'hpy/debug/src/include',
              ],
              extra_compile_args=[
                  '-DHPY_UNIVERSAL_ABI',
                  '-DHPY_DEBUG_ENABLE_UHPY_SANITY_CHECK',
              ] + EXTRA_COMPILE_ARGS
              )
    ]


DEV_REQUIREMENTS = [
    "pytest",
    "pytest-xdist",
]

setup(
    name="hpy",
    author='The HPy team',
    author_email='hpy-dev@python.org',
    url='https://hpyproject.org',
    license='MIT',
    description='A better C API for Python',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    packages = ['hpy.devel', 'hpy.debug'],
    include_package_data=True,
    extras_require={
        "dev": DEV_REQUIREMENTS,
    },
    ext_modules=EXT_MODULES,
    entry_points={
        "distutils.setup_keywords": [
            "hpy_ext_modules = hpy.devel:handle_hpy_ext_modules",
        ],
    },
    use_scm_version=get_scm_config,
    setup_requires=['setuptools_scm'],
)
