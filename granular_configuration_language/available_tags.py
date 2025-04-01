# isort:skip_file
if __name__ == "__main__":
    import argparse
    import operator as op
    import os

    from granular_configuration_language.yaml._tags import handlers
    from granular_configuration_language.yaml.decorators._viewer import AvailableTags, can_table

    choices = ["csv", "json"]
    default = "csv"

    if can_table and (os.environ.get("G_CONFIG_FORCE_CAN_TABLE_FALSE", "FALSE") != "TRUE"):
        choices.append("table")
        default = "table"

    parser = argparse.ArgumentParser(
        prog="python -m granular_configuration_language.available_tags",
        description="Shows available tags",
        epilog=AvailableTags(handlers).table(_force_missing=True),
    )
    parser.add_argument("type", default=default, choices=choices, nargs="?", help=f"Mode, default={{{default}}}")

    args = parser.parse_args()

    print(op.methodcaller(args.type)(AvailableTags(handlers)))
