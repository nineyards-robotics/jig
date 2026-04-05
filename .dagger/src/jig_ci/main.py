"""Dagger CI module for the jig repo.

Exposes three functions:

- ``lint``           — runs pre-commit against the whole repo.
- ``build-and-test`` — colcon build + test inside a ROS 2 base container,
                       parameterised by ROS distro (humble/jazzy/kilted).
- ``ci``             — convenience wrapper that runs ``lint`` then
                       ``build-and-test``.

Call locally from the repo root::

    dagger call lint --src=.
    dagger call build-and-test --src=. --ros-distro=jazzy
    dagger call ci --src=. --ros-distro=jazzy
"""

import dagger
from dagger import dag, function, object_type


def sh(*cmds: str) -> list[str]:
    """Wrap a sequence of shell commands as an argv for ``with_exec``.

    Dagger's ``with_exec`` takes a raw argv, so any step that needs shell
    features (``source``, ``&&``, globs, env expansion) has to go through
    ``bash -c "..."``. This helper keeps that boilerplate in one place:
    callers pass commands as separate strings and we stitch them into a
    single script.

    The script is prefixed with ``set -ex``:

    - ``-e`` aborts on the first non-zero exit, so a failing ``apt-get
      update`` halts the step instead of limping on to a misleading error
      three commands later.
    - ``-x`` echoes each command before running it, which makes CI logs
      self-describing when something goes wrong.

    ``-u`` (error on unset variables) is deliberately *not* set: ROS's
    ``setup.bash`` references ``AMENT_TRACE_SETUP_FILES`` without a
    default and explodes under ``-u``.

    Commands are joined with newlines rather than ``&&``. With ``-e`` in
    effect the two are equivalent for error propagation, but newlines
    avoid doubling up on failure handling and make the ``-x`` trace
    render one command per line instead of a single ``a && b && c`` blob.
    """
    return ["bash", "-c", "\n".join(("set -ex", *cmds))]


@object_type
class JigCi:
    # ------------------------------------------------------------------
    # lint
    # ------------------------------------------------------------------
    @function
    async def lint(self, src: dagger.Directory) -> str:
        """Run pre-commit across the whole repo.

        Pre-commit manages its own hook environments (clang-format,
        cmake-format, black, etc. all come from pinned pip/mirror repos),
        so the only system dep we need is git.
        """
        return await (
            dag.container()
            .from_("python:3.12-slim")
            .with_exec(
                sh(
                    "apt-get update",
                    "DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends git",
                    "rm -rf /var/lib/apt/lists/*",
                    "pip install --no-cache-dir pre-commit",
                )
            )
            .with_mounted_directory("/src", src)
            .with_workdir("/src")
            .with_exec(["pre-commit", "run", "--all-files", "--show-diff-on-failure", "--color", "always"])
            .stdout()
        )

    # ------------------------------------------------------------------
    # build_and_test
    # ------------------------------------------------------------------
    @function
    async def build_and_test(
        self,
        src: dagger.Directory,
        ros_distro: str,
    ) -> str:
        """Build the jig workspace with colcon and run its tests.

        Two-stage pipeline:

        1. **rosdep stage** — only the ``package.xml`` files are mounted
           into the container before ``rosdep install`` runs. apt/rosdep
           resolution is the single most expensive step in a cold build
           (tens of seconds pulling indices + installing system deps), and
           its only real inputs are the ``<depend>`` entries in the
           package manifests. Mounting just the manifests means editing
           any ``.cpp``/``.py``/``CMakeLists.txt`` leaves this layer as a
           cache hit via Dagger's input-hashed per-op cache.

        2. **workspace-wide colcon build + test**, with persistent
           ``CacheVolume`` mounts for ``build/``, ``install/``, ``log/``
           and ccache. Colcon's own incremental machinery (mtime-based
           per-package skip, CMake reconfiguration only where needed)
           decides what to rebuild; ccache covers object-file reuse even
           when CMake does reconfigure or when Dagger's layer cache is
           cold. The cache keys are per-ROS-distro so a humble ``build/``
           never leaks into a jazzy run.

           Trade-off vs. per-package Dagger layers: ``CacheVolume`` is
           mutable shared state, not content-addressed, so a poisoned
           ``build/`` can persist across runs. If that happens, bump the
           cache key suffix or purge the volume. In exchange, adding a
           workspace package requires no changes to this function's
           build loop, and cold-Dagger-cache runs (new branch, cleared
           engine) get a big speedup from ccache that layer caching
           cannot provide.
        """
        image = f"ros:{ros_distro}-ros-base"
        setup = f"source /opt/ros/{ros_distro}/setup.bash"

        # Strip any build artefacts a developer may have left lying around
        # in their working copy. These directories contain absolute host
        # paths (CMakeCache.txt, .pytest_cache entries, etc.) and would
        # poison a fresh in-container build if mounted verbatim. On a clean
        # CI checkout these paths don't exist and without_directory is a
        # no-op.
        for polluted in (
            "build",
            "install",
            "log",
            "jig_cli/tests/test_ws/build",
            "jig_cli/tests/test_ws/install",
            "jig_cli/tests/test_ws/log",
            "jig_cli/.pytest_cache",
            "jig/.pytest_cache",
        ):
            src = src.without_directory(polluted)

        # ------------------------------------------------------------------
        # Stage 1: rosdep install against manifests only.
        #
        # We build a fresh Directory containing *just* the package.xml
        # files at the same relative paths they'd have inside the
        # workspace, then mount that. The glob is depth-limited to
        # ``*/package.xml`` (one level below the repo root) rather than
        # ``**/package.xml``: every real workspace package sits directly
        # under the repo root, while the nested manifests under
        # ``jig_cli/tests/test_ws/src/`` are test fixtures — not real
        # packages — and would pull unnecessary rosdeps if included.
        manifest_paths = await src.glob("*/package.xml")
        if not manifest_paths:
            raise RuntimeError("no workspace package.xml files found at */package.xml")
        manifests = dag.directory()
        for path in manifest_paths:
            manifests = manifests.with_file(path, src.file(path))

        ctr = (
            dag.container()
            .from_(image)
            .with_directory("/ws/src/jig", manifests)
            .with_workdir("/ws")
            # rosdep is pre-initialised in the ros:* images, so just update
            # and resolve dependencies declared in the package.xml files.
            .with_exec(
                sh(
                    "apt-get update",
                    f"rosdep update --rosdistro {ros_distro}",
                    f"rosdep install --from-paths src --ignore-src -y --rosdistro {ros_distro}",
                    "rm -rf /var/lib/apt/lists/*",
                )
            )
        )

        # ------------------------------------------------------------------
        # Stage 2: workspace-wide build + test with persistent caches.
        #
        # Cache keys are scoped per ROS distro — a humble build tree must
        # never be reused under jazzy/kilted (different ABI, different
        # /opt/ros prefix baked into CMake files). Bump the suffix to
        # invalidate if a cache ever gets poisoned.
        cache_key = f"jig-{ros_distro}-v1"
        build_cache = dag.cache_volume(f"{cache_key}-build")
        install_cache = dag.cache_volume(f"{cache_key}-install")
        log_cache = dag.cache_volume(f"{cache_key}-log")
        ccache_vol = dag.cache_volume(f"{cache_key}-ccache")

        ctr = (
            ctr
            # Now overlay the full workspace source. The manifests from
            # stage 1 at /ws/src/jig/<pkg>/package.xml get replaced with
            # the (identical) ones from the full source tree — benign.
            .with_directory("/ws/src/jig", src)
            .with_mounted_cache("/ws/build", build_cache)
            .with_mounted_cache("/ws/install", install_cache)
            .with_mounted_cache("/ws/log", log_cache)
            .with_mounted_cache("/root/.ccache", ccache_vol)
            # Route the compilers through ccache. The ros:*-ros-base
            # images ship ccache symlinks under /usr/lib/ccache; pointing
            # CC/CXX there is enough for CMake's compiler detection to
            # pick them up on first configure.
            .with_env_variable("CC", "/usr/lib/ccache/gcc")
            .with_env_variable("CXX", "/usr/lib/ccache/g++")
            .with_exec(
                sh(
                    setup,
                    "apt-get update",
                    "DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ccache",
                    "rm -rf /var/lib/apt/lists/*",
                    "colcon build --symlink-install --event-handlers console_direct+",
                )
            )
            .with_exec(
                sh(
                    setup,
                    "source install/setup.bash",
                    "colcon test --event-handlers console_direct+ --return-code-on-test-failure",
                    "colcon test-result --verbose",
                )
            )
        )

        return await ctr.stdout()

    # ------------------------------------------------------------------
    # ci
    # ------------------------------------------------------------------
    @function
    async def ci(self, src: dagger.Directory, ros_distro: str) -> str:
        """Run lint then build-and-test. The one-shot local PR check."""
        lint_out = await self.lint(src)
        build_out = await self.build_and_test(src, ros_distro)
        return f"=== lint ===\n{lint_out}\n=== build-and-test ({ros_distro}) ===\n{build_out}"
