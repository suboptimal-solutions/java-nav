"""Integration tests against spring-petclinic (git submodule).

Run with: uv run pytest -m integration -v
Requires: git submodule update --init && mvn -q compile -DskipTests in spring-petclinic
"""

import os
import subprocess

import pytest
from click.testing import CliRunner

from java_nav.cli import main

PETCLINIC_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "spring-petclinic")
PETCLINIC_DIR = os.path.abspath(PETCLINIC_DIR)

pytestmark = pytest.mark.integration
runner = CliRunner()


@pytest.fixture(scope="session", autouse=True)
def ensure_petclinic_compiled():
    """Compile spring-petclinic if submodule is present."""
    pom = os.path.join(PETCLINIC_DIR, "pom.xml")
    if not os.path.isfile(pom):
        pytest.skip("spring-petclinic submodule not initialized")

    classes_dir = os.path.join(PETCLINIC_DIR, "target", "classes")
    if os.path.isdir(classes_dir):
        return  # already compiled

    result = subprocess.run(
        ["mvn", "-q", "compile", "-DskipTests"],
        cwd=PETCLINIC_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Failed to compile spring-petclinic:\n{result.stderr}")


@pytest.fixture
def petclinic():
    return PETCLINIC_DIR


# --- Tier 1: api ---


def test_api_controller(petclinic):
    result = runner.invoke(
        main,
        ["api", "-d", petclinic, "org.springframework.samples.petclinic.owner.OwnerController"],
    )
    assert result.exit_code == 0
    assert "OwnerController" in result.output
    assert "findOwner" in result.output
    assert "processCreationForm" in result.output


def test_api_model_class(petclinic):
    result = runner.invoke(
        main,
        ["api", "-d", petclinic, "org.springframework.samples.petclinic.owner.Owner"],
    )
    assert result.exit_code == 0
    assert "Owner" in result.output


def test_api_spring_dependency(petclinic):
    result = runner.invoke(
        main,
        ["api", "-d", petclinic, "org.springframework.web.bind.annotation.RequestMapping"],
    )
    assert result.exit_code == 0
    assert "RequestMapping" in result.output


# --- Tier 1: source ---


def test_source_project_class(petclinic):
    result = runner.invoke(
        main,
        ["source", "-d", petclinic, "org.springframework.samples.petclinic.owner.OwnerController"],
    )
    assert result.exit_code == 0
    assert "class OwnerController" in result.output
    assert "@Controller" in result.output


def test_source_dependency_class(petclinic):
    result = runner.invoke(
        main,
        ["source", "-d", petclinic, "org.springframework.stereotype.Controller"],
    )
    assert result.exit_code == 0
    assert "public @interface Controller" in result.output


def test_source_line_range(petclinic):
    result = runner.invoke(
        main,
        [
            "source",
            "-d",
            petclinic,
            "org.springframework.samples.petclinic.owner.OwnerController",
            "-l",
            "1:5",
        ],
    )
    assert result.exit_code == 0
    lines = [line for line in result.output.strip().splitlines() if not line.startswith("//")]
    assert len(lines) == 5


# --- Tier 1: grep ---


def test_grep_annotation(petclinic):
    result = runner.invoke(main, ["grep", "-d", petclinic, "@Controller"])
    assert result.exit_code == 0
    assert "OwnerController" in result.output


def test_grep_deps(petclinic):
    result = runner.invoke(main, ["grep", "-d", petclinic, "--deps", "CrudRepository"])
    assert result.exit_code == 0
    assert "CrudRepository" in result.output


# --- Tier 1: deps ---


def test_deps_controller(petclinic):
    result = runner.invoke(
        main,
        ["deps", "-d", petclinic, "org.springframework.samples.petclinic.owner.OwnerController"],
    )
    assert result.exit_code == 0
    assert "spring-web" in result.output
    assert "GetMapping" in result.output


# --- Tier 2: impls ---


def test_impls_spring_repository(petclinic):
    """OwnerRepository/VetRepository should show as implementations of Spring's Repository."""
    result = runner.invoke(
        main,
        ["impls", "-d", petclinic, "org.springframework.data.repository.Repository"],
    )
    assert result.exit_code == 0
    assert "OwnerRepository" in result.output


# --- Tier 2: subtypes ---


def test_subtypes_base_entity(petclinic):
    """PetClinic has a rich hierarchy: BaseEntity → NamedEntity → PetType, Specialty, etc."""
    result = runner.invoke(
        main,
        ["subtypes", "-d", petclinic, "org.springframework.samples.petclinic.model.BaseEntity"],
    )
    assert result.exit_code == 0
    output = result.output
    assert "NamedEntity" in output
    assert "Person" in output
    assert "Owner" in output
    assert "Pet" in output
    assert "Vet" in output


def test_subtypes_named_entity(petclinic):
    result = runner.invoke(
        main,
        ["subtypes", "-d", petclinic, "org.springframework.samples.petclinic.model.NamedEntity"],
    )
    assert result.exit_code == 0
    assert "PetType" in result.output
    assert "Specialty" in result.output
