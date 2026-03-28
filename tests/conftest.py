import os
import subprocess

import pytest

PLAYGROUND_DIR = os.path.join(os.path.dirname(__file__), "..", "playground")
PLAYGROUND_DIR = os.path.abspath(PLAYGROUND_DIR)


@pytest.fixture(scope="session", autouse=True)
def compile_playground():
    """Ensure the playground Java project is compiled before tests run."""
    pom = os.path.join(PLAYGROUND_DIR, "pom.xml")
    if not os.path.isfile(pom):
        pytest.skip("playground project not found")

    result = subprocess.run(
        ["mvn", "-q", "compile"],
        cwd=PLAYGROUND_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Failed to compile playground:\n{result.stderr}")


@pytest.fixture
def playground_dir():
    return PLAYGROUND_DIR
