# isort:skip_file
if __name__ == "__main__":

    import os
    import sys

    from granular_configuration_language.yaml._tags import handlers

    print(
        handlers.pretty(
            as_json=len(sys.argv) < 2,
            width=os.get_terminal_size().columns,
        )
    )
