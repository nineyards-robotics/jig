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

# Keep this list aligned with .github/workflows/ci.yml.
SUPPORTED_DISTROS = ("humble", "jazzy", "kilted")


@object_type
class JigCi:
    # ------------------------------------------------------------------
    # lint
    # ------------------------------------------------------------------
    @function
    async def lint(self, src: dagger.Directory) -> str:
        """Run pre-commit across the whole repo.

        Uses a pinned python:3.12-slim base and installs the system tools
        that pre-commit hooks shell out to (git, clang-format, cmake-format)
        so the hooks don't need to fetch them at runtime.
        """
        return (
            await (
                dag.container()
                .from_("python:3.12-slim")
                .with_exec(
                    [
                        "bash",
                        "-c",
                        (
                            "set -eux && "
                            "apt-get update && "
                            "DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "
                            "git clang-format && "
                            "rm -rf /var/lib/apt/lists/* && "
                            "pip install --no-cache-dir pre-commit"
                        ),
                    ]
                )
                .with_mounted_directory("/src", src)
                .with_workdir("/src")
                # pre-commit requires a git repo to discover files; if the
                # mounted directory isn't one (e.g. when invoked via
                # `dagger call --src=.` from a non-git checkout), synthesise a
                # throwaway one so hooks still run against every tracked file.
                .with_exec(
                    [
                        "bash",
                        "-c",
                        (
                            "set -eux && "
                            "if [ ! -d .git ]; then "
                            "  git init -q -b main && "
                            "  git -c user.email=ci@jig -c user.name=ci add -A && "
                            "  git -c user.email=ci@jig -c user.name=ci commit -q -m seed; "
                            "fi && "
                            "pre-commit run --all-files --show-diff-on-failure --color always"
                        ),
                    ]
                )
                .stdout()
            )
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
        if ros_distro not in SUPPORTED_DISTROS:
            raise ValueError(f"ros_distro must be one of {SUPPORTED_DISTROS}, got {ros_distro!r}")

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

        base = (
            dag.container().from_(image)
            # Tooling that isn't in *-ros-base but is needed for our build.
            .with_exec(
                [
                    "bash",
                    "-c",
                    (
                        "set -eux && "
                        "apt-get update && "
                        "DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "
                        "python3-colcon-common-extensions python3-rosdep python3-pip && "
                        "rm -rf /var/lib/apt/lists/*"
                    ),
                ]
            )
        )

        workspace = (
            base.with_mounted_directory("/ws/src/jig", src).with_workdir("/ws")
            # rosdep is pre-initialised in the ros:* images, so just update
            # and resolve dependencies declared in the package.xml files.
            .with_exec(
                [
                    "bash",
                    "-c",
                    (
                        "set -eux && "
                        "apt-get update && "
                        "rosdep update --rosdistro " + ros_distro + " && "
                        "rosdep install --from-paths src --ignore-src -y "
                        "--rosdistro " + ros_distro + " && "
                        "rm -rf /var/lib/apt/lists/*"
                    ),
                ]
            )
            # colcon build — source setup.bash in the same shell as colcon.
            .with_exec(
                [
                    "bash",
                    "-c",
                    f"set -ex && {setup} && colcon build --symlink-install --event-handlers console_direct+",
                ]
            )
            # colcon test + result summary. Exit non-zero on any failure so
            # Dagger propagates it up as a pipeline failure.
            .with_exec(
                [
                    "bash",
                    "-c",
                    (
                        "set -ex && "
                        f"{setup} && source install/setup.bash && "
                        "colcon test --event-handlers console_direct+ --return-code-on-test-failure && "
                        "colcon test-result --verbose"
                    ),
                ]
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
