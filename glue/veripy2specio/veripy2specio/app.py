import json

from veripy2specio.configuration import Configuration
from veripy2specio.schemas import validate, INPUT_SCHEMA, OUTPUT_SCHEMA


def load_input(config):
    input = json.load(config.input)
    validate(input, INPUT_SCHEMA)
    return input


def dump_output(output, config):
    validate(output, OUTPUT_SCHEMA)
    config.output.write(json.dumps(output))


def transform(input, config):
    # TODO: Write actual transform.
    return input


def main():
    config = Configuration()

    if config.verify_veripy:
        # Don't do any transformation, just validate.
        input = json.load(config.input)
        validate(input, INPUT_SCHEMA)
    elif config.verify_specio:
        # Don't do any transformation, just validate.
        input = json.load(config.input)
        validate(input, OUTPUT_SCHEMA)
    else:
        # Convert the file.
        input = load_input(config)
        output = transform(input, config)
        dump_output(output, config)
