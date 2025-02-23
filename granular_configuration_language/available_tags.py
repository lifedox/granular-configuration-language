# isort:skip_file
if __name__ == "__main__":
    import argparse
    import operator as op

    from granular_configuration_language.yaml._tags import handlers

    choices = ["csv", "json"]
    default = "csv"

    if handlers.can_table:
        choices.append("table")
        default = "table"

    parser = argparse.ArgumentParser(description="Shows available tags", epilog=handlers.table(_force_missing=True))
    parser.add_argument("type", default=default, choices=choices, nargs="?")

    args = parser.parse_args()

    print(op.methodcaller(args.type)(handlers))
