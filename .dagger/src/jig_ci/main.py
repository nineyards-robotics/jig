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
    #
    # Packages in topological build order. ``jig_example`` depends on
    # ``jig`` via ``<depend>jig</depend>`` in its package.xml; ``jig_cli``
    # is pure ament_python with no intra-workspace deps so it can slot in
    # anywhere. Adding a new package here is the one manual step required
    # when the workspace grows.
    PACKAGES: tuple[str, ...] = ("jig", "jig_example", "jig_cli")

    @function
    async def build_and_test(
        self,
        src: dagger.Directory,
        ros_distro: str,
    ) -> str:
        """Build the jig workspace with colcon and run its tests.

        Structured as a layered pipeline so that Dagger's per-operation
        cache can skip work whose inputs haven't changed:

        1. **rosdep stage** — only the ``package.xml`` files are mounted
           into the container before ``rosdep install`` runs. apt/rosdep
           resolution is the single most expensive step in a cold build
           (tens of seconds pulling indices + installing system deps), and
           its only real inputs are the ``<depend>`` entries in the
           package manifests. Mounting just the manifests means editing
           any ``.cpp``/``.py``/``CMakeLists.txt`` leaves this layer as a
           cache hit.

        2. **per-package build + test, interleaved, in topological order**
           — for each package we mount *only that package's* source tree,
           run ``colcon build --packages-select <pkg>``, then
           ``colcon test --packages-select <pkg>``. Dagger hashes each
           ``with_exec`` by ``(parent layer, command, mount contents)``,
           so editing a file inside ``jig_example`` leaves every earlier
           layer (``jig`` build, ``jig`` test, ``jig_cli`` build,
           ``jig_cli`` test) as cache hits and only reruns the
           ``jig_example`` steps.

           Builds and tests are interleaved per package rather than
           "build everything, then test everything" so that a change to a
           *downstream* package's source doesn't invalidate the cached
           test runs of upstream packages. The trade-off is a linear
           chain: editing ``jig`` still invalidates every layer below it,
           which is the correct behaviour (dependents must rebuild)
           rather than a caching deficiency.
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
        # workspace, then mount that. Using an explicit file list (rather
        # than ``include=["**/package.xml"]``) avoids accidentally picking
        # up the nested manifests under ``jig_cli/tests/test_ws/src/``,
        # which are test fixtures — not real workspace packages — and
        # would pull unnecessary rosdeps.
        manifests = dag.directory()
        for pkg in self.PACKAGES:
            manifests = manifests.with_file(f"{pkg}/package.xml", src.file(f"{pkg}/package.xml"))

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
        # Stage 2: per-package build + test, topologically ordered.
        for pkg in self.PACKAGES:
            ctr = (
                ctr
                # Overlay just this package's source on top of the
                # manifests that are already in /ws/src/jig/<pkg>. The
                # package.xml from stage 1 gets replaced with the
                # (identical) one from the full source tree — benign.
                .with_directory(f"/ws/src/jig/{pkg}", src.directory(pkg))
                .with_exec(
                    sh(
                        setup,
                        # If earlier packages have been installed in this
                        # chain, their setup.bash exists — source it so
                        # colcon can find their exported targets. On the
                        # first iteration install/ doesn't exist yet.
                        "[ -f install/setup.bash ] && source install/setup.bash || true",
                        f"colcon build --symlink-install --event-handlers console_direct+ --packages-select {pkg}",
                    )
                )
                .with_exec(
                    sh(
                        setup,
                        "source install/setup.bash",
                        f"colcon test --event-handlers console_direct+ --return-code-on-test-failure --packages-select {pkg}",
                        f"colcon test-result --test-result-base build/{pkg} --verbose",
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
