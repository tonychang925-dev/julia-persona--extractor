from persona_extractor.package.generator import generate_persona_package


def test_generate_persona_package():
    package = generate_persona_package([])
    assert package["manifest"]["schema_version"] == "0.1.0"
