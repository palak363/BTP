"""IIIT Delhi only; kept for existing commands. See build_institutes.py for all institutes."""
from build_institutes import summarize, compare_reference, main as build_main  # noqa: F401


def main():
    build_main(default_only=['IIIT Delhi'])


if __name__ == '__main__':
    main()
