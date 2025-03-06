# isort:skip_file
if __name__ == "__main__":
    import argparse
    import operator as op
    import os

    os.environ["G_CONFIG_ENABLE_TAG_TRACKER"] = "TRUE"

    from granular_configuration_language.yaml._tags import handlers
    from granular_configuration_language.yaml.decorators._viewer import AvailableTags, can_table

    choices = ["csv", "json"]
    default = "csv"

    if can_table:
        choices.append("table")
        default = "table"

    parser = argparse.ArgumentParser(
        description="Shows available tags", epilog=AvailableTags(handlers).table(_force_missing=True)
    )
    parser.add_argument("type", default=default, choices=choices, nargs="?")

    args = parser.parse_args()

    print(op.methodcaller(args.type)(AvailableTags(handlers)))
