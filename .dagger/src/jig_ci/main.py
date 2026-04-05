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

        Mirrors the work the old ``ros-tooling/action-ros-ci`` step was
        doing: drop the source tree into ``/ws/src/jig``, pull dependencies
        via rosdep, then colcon build + test.
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

        workspace = (
            dag.container()
            .from_(image)
            .with_mounted_directory("/ws/src/jig", src)
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
            # colcon build — source setup.bash in the same shell as colcon.
            .with_exec(
                sh(
                    setup,
                    "colcon build --symlink-install --event-handlers console_direct+",
                )
            )
            # colcon test + result summary. Exit non-zero on any failure so
            # Dagger propagates it up as a pipeline failure.
            .with_exec(
                sh(
                    setup,
                    "source install/setup.bash",
                    "colcon test --event-handlers console_direct+ --return-code-on-test-failure",
                    "colcon test-result --verbose",
                )
            )
        )

        return await workspace.stdout()

    # ------------------------------------------------------------------
    # ci
    # ------------------------------------------------------------------
    @function
    async def ci(self, src: dagger.Directory, ros_distro: str) -> str:
        """Run lint then build-and-test. The one-shot local PR check."""
        lint_out = await self.lint(src)
        build_out = await self.build_and_test(src, ros_distro)
        return f"=== lint ===\n{lint_out}\n=== build-and-test ({ros_distro}) ===\n{build_out}"
